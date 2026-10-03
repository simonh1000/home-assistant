import csv
from datetime import datetime, timezone
from pathlib import Path
import pytest
import homeassistant.util.dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

CSV_PATH = Path(__file__).parent / "test1.csv"


def parse_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compute_15min_peaks(
    rows: list[tuple[datetime, float]], pause_windows: list[tuple[datetime, datetime]], ev_power_w: float = 5560.0
) -> dict[str, dict[str, float]]:
    """Calculate fixed 15-minute clock-aligned averages for raw and HA-simulated Guardian control."""
    if not rows:
        return {}

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


async def test_replay_csv_through_ha_engine(hass, setup_ha_guardian, freezer):
    """Replay real-world test1.csv history through Home Assistant's real automation engine."""
    service_calls = setup_ha_guardian

    assert CSV_PATH.exists(), f"CSV file not found at {CSV_PATH}"

    # Read CSV rows
    csv_rows: list[tuple[datetime, float]] = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_rows.append((parse_timestamp(row["last_changed"]), float(row["state"])))

    assert len(csv_rows) > 0, "CSV file is empty"

    # Set initial virtual clock to start of CSV data
    first_ts, first_power = csv_rows[0]
    freezer.move_to(first_ts)
    async_fire_time_changed(hass, first_ts)

    # Initial state setup
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    hass.states.async_set("sensor.p1_meter_power", str(first_power))
    await hass.async_block_till_done()

    pause_windows: list[tuple[datetime, datetime]] = []
    current_pause_start: datetime | None = None

    # Track state change events for clean table output
    state_change_events = []

    last_guardian_state = hass.states.get("input_select.ev_guardian_state").state
    last_charge_mode = hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state

    def generate_explanation(entity: str, from_st: str, to_st: str, power: float) -> str:
        if entity == "ev_guardian_state":
            if from_st == "idle" and to_st == "yielding":
                return "House load >6.0kW, EV paused"
            elif from_st == "yielding" and to_st == "cooldown":
                return "House load dropped, starting cooldown"
            elif from_st == "cooldown" and to_st == "yielding":
                return "House load increased, reverted yielding"
            elif from_st == "idle" and to_st == "cooking":
                return "Dinner window active, EV paused"
            elif from_st == "cooking" and to_st == "idle":
                return "Dinner window ended, state set idle"
            elif to_st == "idle":
                return "Conditions clear, state set idle"
        elif entity == "ev_charge_mode":
            if to_st == "paused":
                return "EV charger set to paused"
            elif to_st == "smart_charge":
                return "EV charger resumed smart charge"
        return f"Transitioned from {from_st} to {to_st}"

    # Replay each historical sensor reading through HA
    for ts, power_w in csv_rows:
        freezer.move_to(ts)
        async_fire_time_changed(hass, ts)
        hass.states.async_set("sensor.p1_meter_power", str(power_w))
        await hass.async_block_till_done()

        curr_guardian_state = hass.states.get("input_select.ev_guardian_state").state
        curr_charge_mode = hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state

        if curr_guardian_state != last_guardian_state:
            explanation = generate_explanation("ev_guardian_state", last_guardian_state, curr_guardian_state, power_w)
            state_change_events.append({
                "ts": ts,
                "entity": "ev_guardian_state",
                "from_state": last_guardian_state,
                "to_state": curr_guardian_state,
                "power_w": power_w,
                "explanation": explanation
            })
            last_guardian_state = curr_guardian_state

        if curr_charge_mode != last_charge_mode:
            explanation = generate_explanation("ev_charge_mode", last_charge_mode, curr_charge_mode, power_w)
            state_change_events.append({
                "ts": ts,
                "entity": "ev_charge_mode",
                "from_state": last_charge_mode,
                "to_state": curr_charge_mode,
                "power_w": power_w,
                "explanation": explanation
            })
            if curr_charge_mode == "paused" and current_pause_start is None:
                current_pause_start = ts
            elif curr_charge_mode != "paused" and current_pause_start is not None:
                pause_windows.append((current_pause_start, ts))
                current_pause_start = None
            last_charge_mode = curr_charge_mode

    if current_pause_start is not None and csv_rows:
        pause_windows.append((current_pause_start, csv_rows[-1][0]))

    # Verify that Home Assistant triggered a PAUSE during high load
    assert len(state_change_events) > 0, "Expected Home Assistant to trigger at least one automation state change"

    # Compute Flanders Capacity Tariff 15-minute peaks
    peaks = compute_15min_peaks(csv_rows, pause_windows)

    max_raw = max(d["raw_avg_w"] for d in peaks.values())
    max_sim = max(d["sim_avg_w"] for d in peaks.values())
    raw_peak_window = [w for w, d in peaks.items() if d["raw_avg_w"] == max_raw][0]
    sim_peak_window = [w for w, d in peaks.items() if d["sim_avg_w"] == max_sim][0]

    peak_above_6k_raw = max(0.0, max_raw - 6000.0)
    peak_above_6k_sim = max(0.0, max_sim - 6000.0)
    peak_avoided = peak_above_6k_raw - peak_above_6k_sim
    annual_savings = (peak_avoided / 1000.0) * 64.6

    print("\n" + "=" * 105)
    print("AUTOMATION STATE CHANGE EVENTS (test1.csv Replay)")
    print("=" * 105)
    print(f"{'WHEN':<10} {'ENTITY':<20} {'FROM STATE':<14} {'TO STATE':<14} {'POWER':<10} {'EXPLANATION'}")
    print("-" * 105)
    for evt in state_change_events:
        ts_str = evt["ts"].strftime("%H:%M:%S")
        pow_str = f"{evt['power_w']:.0f} W"
        print(f"{ts_str:<10} {evt['entity']:<20} {evt['from_state']:<14} {evt['to_state']:<14} {pow_str:<10} {evt['explanation']}")
    print("=" * 105)

    print("\n" + "=" * 105)
    print("FLANDERS CAPACITY TARIFF (15-MINUTE CLOCK-ALIGNED AVERAGES)")
    print("=" * 105)
    print(f"{'WINDOW':<12} {'RAW 15-MIN AVG':<20} {'GUARDIAN HA EMULATED':<25} {'SAVINGS'}")
    print("-" * 105)
    for w, data in peaks.items():
        diff = data['raw_avg_w'] - data['sim_avg_w']
        diff_str = f"-{diff:.0f} W" if diff > 0 else "0 W"
        print(f"{w:<12} {data['raw_avg_w']:<20.1f} W {data['sim_avg_w']:<25.1f} W {diff_str}")
    print("-" * 105)
    print(f"MAX RAW 15-MIN PEAK      : {max_raw:.1f} W ({max_raw/1000:.2f} kW) [Window: {raw_peak_window}]")
    print(f"MAX GUARDIAN HA PEAK     : {max_sim:.1f} W ({max_sim/1000:.2f} kW) [Window: {sim_peak_window}]")
    print(f"PEAK ABOVE 6kW AVOIDED   : {peak_avoided:.1f} W ({peak_avoided/1000:.2f} kW)")
    print(f"ESTIMATED TARIFF SAVINGS : ~€{annual_savings:.2f} / year")
    print("=" * 105)

    # Assert that peak power above 6.0 kW was successfully prevented by HA automation
    assert max_sim <= 6000.0, f"Guardian HA emulation failed to keep peak below 6.0 kW (Max peak was {max_sim:.1f} W)"
