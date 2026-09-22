"""Python prototype/simulator matching ev-capacity-guardian.yaml and ev-cooking-over.yaml.

Models the 3-state enum machine:
  - input_select.ev_guardian_state: idle | yielding | cooldown
  - input_boolean.ev_cooking_over: True | False
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum


class GuardianState(str, Enum):
    IDLE = "idle"
    YIELDING = "yielding"
    COOLDOWN = "cooldown"


class OhmeStatus(str, Enum):
    CHARGING = "charging"
    PAUSED = "paused"
    FINISHED = "finished"
    PLUGGED_IN = "plugged_in"
    UNPLUGGED = "unplugged"


class OhmeChargeMode(str, Enum):
    SMART_CHARGE = "smart_charge"
    PAUSED = "paused"


@dataclass(frozen=True)
class Decision:
    timestamp: datetime
    action: str  # "PAUSE", "RESUME", "STATE_CHANGE", "ALERT"
    from_state: GuardianState
    to_state: GuardianState
    reason: str
    power_w: float
    cooking_over: bool = False


@dataclass
class Policy:
    high_load_w: float = 6000.0
    high_load_for_s: float = 30.0
    quiet_load_w: float = 500.0
    quiet_for_s: float = 120.0
    noisy_load_w: float = 800.0
    noisy_for_s: float = 15.0
    minimum_pause_s: float = 600.0
    dinner_start: time = time(18, 15)
    dinner_end: time = time(20, 0)
    safety_net: time = time(22, 30)


class GuardianSimulator:
    """State machine simulator strictly mirroring ev-capacity-guardian.yaml."""

    def __init__(self, policy: Policy = Policy()) -> None:
        self.policy = policy
        self.state = GuardianState.IDLE
        self.cooking_over = False
        self.charge_mode = OhmeChargeMode.SMART_CHARGE
        
        self._yielding_start_time: datetime | None = None
        self._last_timestamp: datetime | None = None
        self._high_duration_s = 0.0
        self._quiet_duration_s = 0.0
        self._noisy_duration_s = 0.0
        self._decisions: list[Decision] = []

    @property
    def decisions(self) -> list[Decision]:
        return list(self._decisions)

    def trigger_cooking_over(self, at: datetime, current_ohme_status: OhmeStatus, power_w: float = 0.0) -> list[Decision]:
        """Simulate user pressing 'Cooking Over' button (ev-cooking-over.yaml)."""
        decisions: list[Decision] = []
        old_state = self.state
        self.cooking_over = True
        self.state = GuardianState.IDLE
        self._yielding_start_time = None

        if current_ohme_status == OhmeStatus.PAUSED:
            self.charge_mode = OhmeChargeMode.SMART_CHARGE
            d = Decision(
                timestamp=at,
                action="RESUME",
                from_state=old_state,
                to_state=self.state,
                reason="Cooking window ended manually — EV charging resumed",
                power_w=power_w,
                cooking_over=self.cooking_over,
            )
            decisions.append(d)
            self._decisions.append(d)
        return decisions

    def observe(
        self,
        at: datetime,
        power_w: float,
        current_ohme_status: OhmeStatus,
    ) -> list[Decision]:
        """Process one timestamped P1 power reading and return triggered decisions."""
        if self._last_timestamp is not None:
            delta_s = (at - self._last_timestamp).total_seconds()
            if delta_s < 0:
                raise ValueError("Timestamps must be non-decreasing")
        else:
            delta_s = 0.0

        self._last_timestamp = at
        decisions: list[Decision] = []

        # Update load counters
        if power_w > self.policy.high_load_w:
            self._high_duration_s += delta_s
        else:
            self._high_duration_s = 0.0

        if power_w < self.policy.quiet_load_w:
            self._quiet_duration_s += delta_s
        else:
            self._quiet_duration_s = 0.0

        if power_w > self.policy.noisy_load_w:
            self._noisy_duration_s += delta_s
        else:
            self._noisy_duration_s = 0.0

        current_time = at.time()

        # Rule 8: Safety net at 22:30
        if current_time >= self.policy.safety_net and self.state != GuardianState.IDLE:
            old_state = self.state
            self.state = GuardianState.IDLE
            self._yielding_start_time = None
            if current_ohme_status == OhmeStatus.PAUSED:
                self.charge_mode = OhmeChargeMode.SMART_CHARGE
                d = Decision(
                    timestamp=at,
                    action="RESUME",
                    from_state=old_state,
                    to_state=self.state,
                    reason="22:30 safety net — resumed regardless of state",
                    power_w=power_w,
                    cooking_over=self.cooking_over,
                )
                decisions.append(d)

        # Rule 6: Dinner window end at 20:00
        if current_time >= self.policy.dinner_end and self.cooking_over:
            self.cooking_over = False

        if current_time >= self.policy.dinner_end and self.state == GuardianState.IDLE and current_ohme_status == OhmeStatus.PAUSED:
            old_state = self.state
            self.charge_mode = OhmeChargeMode.SMART_CHARGE
            d = Decision(
                timestamp=at,
                action="RESUME",
                from_state=old_state,
                to_state=self.state,
                reason="Dinner window end — resumed",
                power_w=power_w,
                cooking_over=self.cooking_over,
            )
            decisions.append(d)

        # Rule 1 & 2: High house load collision
        if self._high_duration_s >= self.policy.high_load_for_s:
            if current_ohme_status == OhmeStatus.CHARGING and self.charge_mode != OhmeChargeMode.PAUSED:
                old_state = self.state
                self.charge_mode = OhmeChargeMode.PAUSED
                self.state = GuardianState.YIELDING
                self._yielding_start_time = at
                self._quiet_duration_s = 0.0
                d = Decision(
                    timestamp=at,
                    action="PAUSE",
                    from_state=old_state,
                    to_state=self.state,
                    reason="House load stayed above 6.0kW for 30s. EV paused.",
                    power_w=power_w,
                    cooking_over=self.cooking_over,
                )
                decisions.append(d)
                self._high_duration_s = 0.0

        # Rule 3: Dinner lockout (18:15 - 20:00)
        is_dinner = self.policy.dinner_start <= current_time < self.policy.dinner_end
        if is_dinner and not self.cooking_over and current_ohme_status == OhmeStatus.CHARGING and self.charge_mode != OhmeChargeMode.PAUSED:
            old_state = self.state
            self.charge_mode = OhmeChargeMode.PAUSED
            d = Decision(
                timestamp=at,
                action="PAUSE",
                from_state=old_state,
                to_state=self.state,
                reason="Paused for the dinner window",
                power_w=power_w,
                cooking_over=self.cooking_over,
            )
            decisions.append(d)

        # Rule 4: Quiet house confirmation (yielding -> cooldown)
        if self.state == GuardianState.YIELDING and self._quiet_duration_s >= self.policy.quiet_for_s:
            old_state = self.state
            self.state = GuardianState.COOLDOWN
            d = Decision(
                timestamp=at,
                action="STATE_CHANGE",
                from_state=old_state,
                to_state=self.state,
                reason="House draw dropped below 500W for 2m — cooldown started",
                power_w=power_w,
                cooking_over=self.cooking_over,
            )
            decisions.append(d)

        # Rule 5: House load rise during cooldown (cooldown -> yielding)
        if self.state == GuardianState.COOLDOWN and self._noisy_duration_s >= self.policy.noisy_for_s:
            old_state = self.state
            self.state = GuardianState.YIELDING
            d = Decision(
                timestamp=at,
                action="STATE_CHANGE",
                from_state=old_state,
                to_state=self.state,
                reason="House load exceeded 800W for 15s — reverted to yielding",
                power_w=power_w,
                cooking_over=self.cooking_over,
            )
            decisions.append(d)

        # Rule 7: Collision recovery (cooldown -> idle after 10m yielding)
        not_dinner = not is_dinner
        if not_dinner and self.state == GuardianState.COOLDOWN and self._yielding_start_time is not None:
            elapsed_s = (at - self._yielding_start_time).total_seconds()
            if elapsed_s >= self.policy.minimum_pause_s and current_ohme_status == OhmeStatus.PAUSED:
                old_state = self.state
                self.charge_mode = OhmeChargeMode.SMART_CHARGE
                self.state = GuardianState.IDLE
                self._yielding_start_time = None
                d = Decision(
                    timestamp=at,
                    action="RESUME",
                    from_state=old_state,
                    to_state=self.state,
                    reason="House quiet and Guardian minimum pause elapsed",
                    power_w=power_w,
                    cooking_over=self.cooking_over,
                )
                decisions.append(d)

        self._decisions.extend(decisions)
        return decisions
