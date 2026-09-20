# Car Charging — Smart Charging Plan

## Objective

Keep home charging compatible with a sensible Flemish capacity-tariff peak while
still allowing a roughly 70% overnight top-up when needed. The charger should
remain fast at public charge points; any home limit belongs at the charger or in
home control, not in the car.

Ladenburgers: EF HD-P3-6K0-S1 — that's a 6kW model

## What matters

- Fluvius uses the highest **fixed 15-minute average import** in each calendar
  month. The capacity charge then reflects the rolling average of monthly peaks,
  subject to a 2.5 kW minimum.
- Normal background use is about 0.2–0.3 kW. Home EV charging is about
  5.5 kW, so the meaningful risk is a substantial appliance running at the same
  time as the car. A refrigerator or freezer can create a sharp but brief spike and should not
  cause an EV pause.
- The EV/house collision, rather than a continuously high house load, explains
  the unwanted peaks.

## Primary protection: charger load balancing

The preferred control is the Ohme's local CT-clamp load balancing. It can react
locally; Home Assistant can only set charge mode through the cloud and is a
backstop, not a real-time current controller.

The charger was configured with a 32 A load limit after the 3-phase upgrade.
That cannot protect a car limited to 11 kW: `32 A × 3 × 230 V = 22.1 kW`.
The intended configuration is:

- Load limit: **10 A per phase** (about 6.9 kW total), if supported.
- Maximum charge current: retain **16 A per phase**.
- Vehicle charge-current cap: remove the old 8 A cap after the charger setting
  is confirmed, so public AC charging remains fast.

This depends on correctly installed clamps. They must cover all three phases and
measure **net grid import**. Verify this by switching known loads on across the
relevant circuits and checking that the clamp reading changes. Correct net-import
placement also makes the scheme compatible with solar generation.

## Proposed Guardian algorithm

Guardian is a simple Home Assistant backstop. It does not try to optimise every
second of a quarter-hour or continuously vary charging current.

1. **Reserve known cooking periods.** Pause the EV during the chosen dinner
   window. This is the predictable high-demand period. 18:15 - 20:00 has been selected.
2. **Otherwise, allow charging.** Treat the EV's ~5.5 kW plus normal background
   load as the ordinary state.
3. **Detect a collision.** While the EV status is `charging`, pause it if total
   P1 import stays above **6.0 kW** for a short confirmation period, initially
   **30 seconds**. This filters brief compressor spikes while reacting to a
   sustained appliance load.
4. **Hold, then retry.** Keep the EV paused for a minimum period (initially
   10 minutes). Resume only after total P1 import has remained below **0.5 kW**
   for a short sustained period (initially 1–2 minutes). That indicates that the
   additional appliance has finished and only ordinary background load remains.
5. **Avoid cycling.** After resuming, apply a short grace period before another
   normal collision decision. A sustained high load still pauses the EV again;
   transient spikes do not.
6. **Notify rather than misattribute.** If P1 import is high while the EV is not
   charging, notify that the high load is not caused by the EV.

These starting values are policy choices, not guarantees. The Ohme cloud command
has delay, so a sudden load can still affect the current 15-minute quarter. The
algorithm is intended to prevent a sustained overlap from becoming the normal
case, while keeping the rules understandable and testable.

## Testing and evidence

The `guardian/` directory contains an algorithm prototype and CSV replay tool.
For each future event, export P1 history and record the Ohme status (and, if
available, EV power). Replay should show whether the 30-second collision rule
would pause at the right time and whether the restart rule would be too eager.

Do not rely on a P1-only replay to say exactly what the resulting tariff peak
would have been: after a simulated pause, it does not know the actual non-EV
load or the cloud-command delay. The useful first comparison is the timing and
reason for each proposed pause; an EV-power-aware model can come later if needed.

## Operating assumptions and open checks

- Set a charge-by time (typically 07:00) and plug in early for a large overnight
  charge. Exact vehicle SoC is not required for the control rules.
- Keep dishwasher, washing machine and dryer out of the EV window where practical.
- Confirm the Ohme load-limit minimum, clamp coverage, clamp placement and actual
  main-fuse rating with the installer.
- Revisit the policy when solar, heat-pump backup heat or other major flexible
  loads materially change the household pattern.

## Capacity tariff — the mechanics, for reference

- Fluvius records the highest quarter-hour _average_ import each calendar month. The annual charge = average of the 12 monthly peaks (minimum 2.5 kW) × rate.
- 2026 Flanders reference rate: **~€53.39/kW/yr excl. VAT** (regional range ~€49–57); **≈ €64.6/kW/yr incl. VAT**.
- A bad month is only ever 1/12th as costly as it feels — it only adds that fraction of its excess to the rolling 12-month average, and fades out again if not repeated.
- Corollary: any charging done before a tariff month closes, at or below the peak already reached that month, costs nothing extra.
- **Current data:** see Fact Sheet → Measured Peak History for the actual monthly figures and rolling averages — kept there so this doc doesn't go stale as new months arrive.

## The fix: one number governs (almost) everything

Ohme's load balancing caps _total_ current through the monitored point, not just the car, so:

**peak (kW) ≈ LOAD LIMIT (A) × 3 × 230 V**, once all three phases are correctly monitored.

Annual capacity-tariff cost is linear — €53.39/kW/yr excl. VAT (≈€64.6/kW/yr incl.) above the 2.5 kW minimum, with no cliff or threshold to dodge. So the table below gives the _absolute_ annual cost at each ceiling, not a cost "extra above baseline" — that framing doesn't hold once load balancing is actually capping total draw, since the ceiling then governs the peak directly regardless of what the rest of the house is doing:

| LOAD LIMIT             | Total ceiling | Annual capacity cost (from 2.5 kW floor, incl. VAT) | Car gets, house quiet | Time for 70% top-up   |
| ---------------------- | ------------- | --------------------------------------------------- | --------------------- | --------------------- |
| 8 A                    | 5.52 kW       | ~€195/yr                                            | 4.55 kW               | ~15.4 h               |
| 9 A                    | 6.21 kW       | ~€239/yr                                            | 5.24 kW               | ~13.3 h               |
| **10 A — recommended** | **6.90 kW**   | **~€284/yr**                                        | **5.93 kW**           | **~11.8 h**           |
| 11 A                   | 7.59 kW       | ~€329/yr                                            | 6.62 kW               | ~10.6 h               |
| 12 A                   | 8.28 kW       | ~€373/yr                                            | 7.31 kW               | ~9.6 h                |
| 32 A (current setting) | 22.16 kW      | n/a — never a real ceiling                          | 11.0 kW (car-limited) | ~6.9 h, no protection |

**Recommendation stands: LOAD LIMIT = 10 A per phase, MAX CHARGE CURRENT stays at 16 A** so the load limit is the actual governor. Modelled against a realistic 17:30–07:00 evening with ~2.5 hours lost/reduced to cooking: ~68 kWh at the meter ≈ 61 kWh to the battery ≈ 70% of gross capacity — meets the target with margin, self-managing (full speed when the house is quiet, throttled during dinner, back up after), no scheduling or SoC visibility required.

**Fallback:** if LOAD LIMIT can't go that low, or the CT clamps prove unreliable, cap MAX CHARGE CURRENT at 8 A instead — cruder, no adaptive behaviour, but bounded by physics rather than by a sensor that might be blind.

## Capacity tariff — the mechanics, for reference

- Fluvius records the highest quarter-hour _average_ import each calendar month. The annual charge = average of the 12 monthly peaks (minimum 2.5 kW) × rate.
- 2026 Flanders reference rate: **~€53.39/kW/yr excl. VAT** (regional range ~€49–57); **≈ €64.6/kW/yr incl. VAT**.
- A bad month is only ever 1/12th as costly as it feels — it only adds that fraction of its excess to the rolling 12-month average, and fades out again if not repeated.
- Corollary: any charging done before a tariff month closes, at or below the peak already reached that month, costs nothing extra.
- **Current data:** see Fact Sheet → Measured Peak History for the actual monthly figures and rolling averages — kept there so this doc doesn't go stale as new months arrive.

## Reference: Amps ↔ kW ↔ kWh

Different sources — the car's menu, the Ohme app, electricians, public charge points — quote "amps" against single-phase, three-phase, or leave it ambiguous, which is the main source of confusion in this whole topic. Two things to always pin down: (1) is a given amp figure _per phase_ or for the whole circuit, and (2) how many phases.

**Single-phase (230 V)** — `kW = 230 × A ÷ 1000`

| Current                       | Power   | Time for a 70% top-up (~68 kWh at meter) |
| ----------------------------- | ------- | ---------------------------------------- |
| 6 A                           | 1.38 kW | ~49 h                                    |
| 8 A                           | 1.84 kW | ~37 h                                    |
| 10 A                          | 2.30 kW | ~30 h                                    |
| 13 A (typical "granny cable") | 2.99 kW | ~23 h                                    |
| 16 A (old home setup)         | 3.68 kW | ~18.5 h                                  |
| 20 A                          | 4.60 kW | ~15 h                                    |
| 32 A                          | 7.36 kW | ~9 h                                     |

**Three-phase (230 V per phase)** — `kW = 3 × 230 × A ÷ 1000` (A is the _per-phase_ figure)

| Current (per phase)               | Power       | Time for a 70% top-up (~68 kWh at meter) | Note                                                                                                                                |
| --------------------------------- | ----------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 6 A (Ohme/car minimum)            | 4.14 kW     | ~16.5 h                                  |                                                                                                                                     |
| 7 A                               | 4.83 kW     | ~14.1 h                                  |                                                                                                                                     |
| 8 A                               | 5.52 kW     | ~12.3 h                                  |                                                                                                                                     |
| 9 A                               | 6.21 kW     | ~11.0 h                                  |                                                                                                                                     |
| **10 A — recommended LOAD LIMIT** | **6.90 kW** | **~9.9 h**                               | fits 17:30–07:00 with cooking allowed for                                                                                           |
| 12 A                              | 8.28 kW     | ~8.2 h                                   |                                                                                                                                     |
| 16 A (car's OBC ceiling)          | 11.04 kW    | ~6.2 h                                   | XPeng G6 On-Board Charger maxes out here — more current from the charger or grid buys nothing beyond this                           |
| 32 A (Ohme's current setting)     | 22.16 kW    | n/a                                      | never reachable — car is hard-capped at 16 A/11 kW by its own OBC, so this setting has given zero protection since the 3F+N upgrade |
