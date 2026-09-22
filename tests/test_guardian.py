"""Unit tests for EV Capacity Guardian 3-state machine."""

import unittest
from datetime import datetime, time, timezone
from tests.guardian_engine import (
    GuardianSimulator,
    GuardianState,
    OhmeStatus,
    Policy,
)

# Sept 19 peak (caused 6.3KW capacity peak)
class TestGuardianStateMachine(unittest.TestCase):
    def setUp(self) -> None:
        self.sim = GuardianSimulator()
        self.base_time = datetime(2026, 9, 21, 14, 0, 0, tzinfo=timezone.utc)

    def test_initial_state_is_idle(self) -> None:
        self.assertEqual(self.sim.state, GuardianState.IDLE)
        self.assertFalse(self.sim.cooking_over)

    def test_high_load_triggers_yielding(self) -> None:
        t0 = self.base_time
        self.sim.observe(t0, 6500.0, OhmeStatus.CHARGING)
        
        # Advance 35 seconds at 6500W
        t1 = datetime(2026, 9, 21, 14, 0, 35, tzinfo=timezone.utc)
        decisions = self.sim.observe(t1, 6500.0, OhmeStatus.CHARGING)
        
        self.assertEqual(self.sim.state, GuardianState.YIELDING)
        self.assertTrue(any(d.action == "PAUSE" for d in decisions))

    def test_yielding_to_cooldown_transition(self) -> None:
        t0 = self.base_time
        self.sim.observe(t0, 6500.0, OhmeStatus.CHARGING)
        t1 = datetime(2026, 9, 21, 14, 0, 35, tzinfo=timezone.utc)
        self.sim.observe(t1, 6500.0, OhmeStatus.CHARGING)
        self.assertEqual(self.sim.state, GuardianState.YIELDING)

        # Drop to 300W for 130s (>120s quiet threshold)
        t2 = datetime(2026, 9, 21, 14, 2, 50, tzinfo=timezone.utc)
        decisions = self.sim.observe(t2, 300.0, OhmeStatus.PAUSED)

        self.assertEqual(self.sim.state, GuardianState.COOLDOWN)
        self.assertTrue(any(d.action == "STATE_CHANGE" for d in decisions))

    def test_cooldown_reverts_to_yielding_on_load_spike(self) -> None:
        # Move to cooldown
        t0 = self.base_time
        self.sim.observe(t0, 6500.0, OhmeStatus.CHARGING)
        t1 = datetime(2026, 9, 21, 14, 0, 35, tzinfo=timezone.utc)
        self.sim.observe(t1, 6500.0, OhmeStatus.CHARGING)
        t2 = datetime(2026, 9, 21, 14, 2, 50, tzinfo=timezone.utc)
        self.sim.observe(t2, 300.0, OhmeStatus.PAUSED)
        self.assertEqual(self.sim.state, GuardianState.COOLDOWN)

        # Load spikes to 900W for 20s (>15s noisy threshold)
        t3 = datetime(2026, 9, 21, 14, 3, 15, tzinfo=timezone.utc)
        decisions = self.sim.observe(t3, 900.0, OhmeStatus.PAUSED)

        self.assertEqual(self.sim.state, GuardianState.YIELDING)
        self.assertTrue(any("reverted to yielding" in d.reason for d in decisions))

    def test_cooldown_resumes_charging_after_minimum_pause(self) -> None:
        t0 = self.base_time
        self.sim.observe(t0, 6500.0, OhmeStatus.CHARGING)
        t1 = datetime(2026, 9, 21, 14, 0, 35, tzinfo=timezone.utc)
        self.sim.observe(t1, 6500.0, OhmeStatus.CHARGING)
        t2 = datetime(2026, 9, 21, 14, 2, 50, tzinfo=timezone.utc)
        self.sim.observe(t2, 300.0, OhmeStatus.PAUSED)
        self.assertEqual(self.sim.state, GuardianState.COOLDOWN)

        # Advance past 10 min minimum pause (600s after t1 = 14:10:35)
        t3 = datetime(2026, 9, 21, 14, 10, 40, tzinfo=timezone.utc)
        decisions = self.sim.observe(t3, 300.0, OhmeStatus.PAUSED)

        self.assertEqual(self.sim.state, GuardianState.IDLE)
        self.assertTrue(any(d.action == "RESUME" for d in decisions))

    def test_cooking_over_override_bypasses_dinner(self) -> None:
        dinner_time = datetime(2026, 9, 21, 18, 30, 0, tzinfo=timezone.utc)
        self.sim.observe(dinner_time, 400.0, OhmeStatus.CHARGING)
        
        # Trigger Cooking Over
        decisions = self.sim.trigger_cooking_over(dinner_time, OhmeStatus.PAUSED)
        self.assertTrue(self.sim.cooking_over)
        self.assertEqual(self.sim.state, GuardianState.IDLE)


if __name__ == "__main__":
    unittest.main()
