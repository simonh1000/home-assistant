"""CSV History Replay runner for EV Capacity Guardian state machine.

Calculates decisions and fixed 15-minute Flanders Capacity Tariff peak averages.

Usage:
    python3 -m tests.replay [tests/test1.csv] [--ev-power-w 5560]
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from tests.guardian_engine import (
    GuardianSimulator,
    OhmeStatus,
    Policy,
)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def replay_csv(csv_path: Path, policy: Policy, ev_is_charging: bool = True) -> GuardianSimulator:
    simulator = GuardianSimulator(policy)
    status = OhmeStatus.CHARGING if ev_is_charging else OhmeStatus.UNPLUGGED

    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ts = parse_timestamp(row["last_changed"])
            power_w = float(row["state"])
            simulator.observe(ts, power_w, current_ohme_status=status)

    return simulator


def compute_15min_peaks(
    csv_path: Path, simulator: GuardianSimulator, ev_power_w: float = 5560.0
) -> dict[str, dict[str, float]]:
    """Calculate fixed 15-minute clock-aligned averages for raw and simulated Guardian control."""
    rows: list[tuple[datetime, float]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((parse_timestamp(r["last_changed"]), float(r["state"])))

    if not rows:
        return {}

    pause_windows: list[tuple[datetime, datetime]] = []
    current_pause_start: datetime | None = None

    for d in simulator.decisions:
        if d.action == "PAUSE" and current_pause_start is None:
            current_pause_start = d.timestamp
        elif d.action == "RESUME" and current_pause_start is not None:
            pause_windows.append((current_pause_start, d.timestamp))
            current_pause_start = None

    if current_pause_start is not None and rows:
        pause_windows.append((current_pause_start, rows[-1][0]))

    def is_paused_at(t: datetime) -> bool:
        return any(start <= t <= end for start, end in pause_windows)

    raw_windows: dict[datetime, list[float]] = {}
    sim_windows: dict[datetime, list[float]] = {}

    for i in range(len(rows) - 1):
        t1, p1 = rows[i]
        t2, _ = rows[i + 1]

        curr = t1
        while curr < t2:
            minute_bucket = (curr.minute // 15) * 15
            bucket_start = curr.replace(minute=minute_bucket, second=0, microsecond=0)
            if minute_bucket < 45:
                bucket_end = bucket_start.replace(minute=minute_bucket + 15)
            else:
                bucket_end = bucket_start.replace(
                    hour=(bucket_start.hour + 1) % 24, minute=0
                )

            slice_end = min(t2, bucket_end)
            slice_dur = (slice_end - curr).total_seconds()

            raw_windows.setdefault(bucket_start, [0.0, 0.0])
            raw_windows[bucket_start][0] += p1 * slice_dur
            raw_windows[bucket_start][1] += slice_dur

            p_sim = max(0.0, p1 - ev_power_w) if is_paused_at(curr) else p1
            sim_windows.setdefault(bucket_start, [0.0, 0.0])
            sim_windows[bucket_start][0] += p_sim * slice_dur
            sim_windows[bucket_start][1] += slice_dur

            curr = slice_end

    results = {}
    for bucket in sorted(raw_windows.keys()):
        raw_energy, raw_dur = raw_windows[bucket]
        sim_energy, sim_dur = sim_windows[bucket]
        raw_avg = raw_energy / raw_dur if raw_dur > 0 else 0.0
        sim_avg = sim_energy / sim_dur if sim_dur > 0 else 0.0
        results[bucket.strftime("%H:%M")] = {
            "raw_avg_w": raw_avg,
            "sim_avg_w": sim_avg,
            "duration_s": raw_dur,
        }

    return results


def main() -> None:
    default_history = Path(__file__).parent / "test1.csv"
    parser = argparse.ArgumentParser(description="Replay P1 history CSV through Guardian state machine")
    parser.add_argument("history", type=Path, nargs="?", default=default_history, help="Path to P1 history CSV file (default: tests/test1.csv)")
    parser.add_argument("--ev-power-w", type=float, default=5560.0, help="EV charging power in Watts (default: 5560 W / 8A 3-phase)")
    args = parser.parse_args()

    if not args.history.exists():
        print(f"Error: File '{args.history}' not found.")
        return

    simulator = replay_csv(args.history, Policy())

    print(f"\nReplaying '{args.history}' through EV Capacity Guardian State Machine...")
    print("=" * 90)
    print(f"{'TIMESTAMP':<12} {'ACTION':<14} {'FROM_STATE':<12} {'TO_STATE':<12} {'POWER':<8} {'REASON'}")
    print("-" * 90)

    for d in simulator.decisions:
        ts_str = d.timestamp.strftime("%H:%M:%S")
        print(f"{ts_str:<12} {d.action:<14} {d.from_state.value:<12} {d.to_state.value:<12} {d.power_w:<8.0f} {d.reason}")

    print("=" * 90)
    print(f"Total Decisions: {len(simulator.decisions)}")

    # 15-Minute Flanders Capacity Tariff Peak Analysis
    peaks = compute_15min_peaks(args.history, simulator, ev_power_w=args.ev_power_w)
    if peaks:
        print("\n" + "=" * 90)
        print("FLANDERS CAPACITY TARIFF (15-MINUTE CLOCK-ALIGNED AVERAGES)")
        print("=" * 90)
        print(f"{'WINDOW':<15} {'DURATION':<12} {'RAW AVERAGE':<16} {'GUARDIAN (SIMULATED)':<22} {'SAVINGS'}")
        print("-" * 90)

        max_raw = 0.0
        max_sim = 0.0
        max_raw_win = ""
        max_sim_win = ""

        for window, data in peaks.items():
            dur_m = data['duration_s'] / 60.0
            raw_w = data['raw_avg_w']
            sim_w = data['sim_avg_w']
            diff_w = raw_w - sim_w

            if raw_w > max_raw:
                max_raw = raw_w
                max_raw_win = window
            if sim_w > max_sim:
                max_sim = sim_w
                max_sim_win = window

            diff_str = f"-{diff_w:.0f} W" if diff_w > 0 else "0 W"
            print(f"{window:<15} {dur_m:<12.1f}m {raw_w:<16.1f} W {sim_w:<22.1f} W {diff_str}")

        print("-" * 90)
        print(f"MAX RAW 15-MIN PEAK      : {max_raw:.1f} W  ({max_raw/1000:.2f} kW)  [Window: {max_raw_win}]")
        print(f"MAX GUARDIAN SIM PEAK    : {max_sim:.1f} W  ({max_sim/1000:.2f} kW)  [Window: {max_sim_win}]")
        peak_reduction = max_raw - max_sim
        if peak_reduction > 0:
            annual_savings = (peak_reduction / 1000.0) * 64.6
            print(f"NET PEAK REDUCTION       : {peak_reduction:.1f} W  ({peak_reduction/1000.0:.2f} kW)")
            print(f"ESTIMATED TARIFF SAVINGS : ~€{annual_savings:.2f} / year (at €64.6/kW/yr incl. VAT)")
        print("=" * 90)


if __name__ == "__main__":
    main()
