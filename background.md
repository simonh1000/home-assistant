# Car Charging — Smart Charging Plan

## Objectives

- Keep to reasonable Flemish capacity rate at home, but be able to add — say — 70% electricity overnight
- Ensure fast charging at the supermarket, …
- Make slow charging as fast as possible from public charge points
- Work out the rules to apply to other devices that might run at night, such as the dishwasher
- Control(?) from the HomeAssistant
- Work out what rules apply after the solar panels have been implemented, as the car is often parked at home during the middle of the day

## The two real-world charging scenarios

1. **Routine day-to-day.** Small top-ups. Car often home during the day, especially once solar goes live (install Wed 26 Aug 2026).
2. **The "empty at 5–6pm, full by 7am" event.** Happens roughly every couple of weeks. The real usable window is **20:30 → 07:00 (13.5 hours)**, not the tighter "overnight" figure it feels like. Target: ~70% into the battery ≈ 61 kWh, ≈ 68 kWh at the meter after AC charging losses (~90% efficiency assumed).

## Diagnosis: why August happened

Checked the Ohme app's Advanced Settings (22 Aug 2026):

| Setting | Value |
|---|---|
| MAX CHARGE CURRENT | 16 A |
| LOAD LIMIT | 32 A |
| CT CLAMP READING | 1.4 A |
| Load Balancing | On |

**LOAD LIMIT 32 A on three phases = 22.1 kW.** The car (capped at 11 kW by its own onboard charger) can never get anywhere near that ceiling, so load balancing has been switched on but structurally unable to ever engage since the 3F+N upgrade.

Both figures read like a **leftover single-phase configuration**: 16 A single-phase = 3.68 kW, matching the "3.7 kW" charge rate from before the upgrade; 32 A single-phase = 7.4 kW, a sensible main-fuse figure. The installer almost certainly never returned to the config after converting us to 3F+N — he owes us this fix. **Top priority — steps already underway.**

The Fact Sheet's Measured Peak History confirms the pattern from actual Fluvius data: monthly peaks sat around 4.6–5.4 kW from **February 2026** on (consistent with routine single-phase-era EV charging plus normal household load — already elevated versus the pre-EV-charging historical baseline, but nothing alarming). Daily-totals data pins the first home charging sessions to **~12 Feb 2026** (see Fact Sheet, Average Daily Electricity Use) — earlier than previously thought, and closer together than the "every couple of weeks" pattern described in Objectives, at least during this initial period. July jumped to a peak well above that range on the back of just two unusually large days in an otherwise very quiet month — consistent with an early, uncontrolled high-power test soon after the 3F+N conversion, rather than routine use. August then produced the extreme outlier — the car-plus-cooking coincidence described below. Two separate incidents, same root cause: nothing was bounding the charger's current draw against the rest of the house. (Full monthly figures: Fact Sheet → Measured Peak History.)

**What we tried and why it didn't work:**

- *15-minute on/off duty-cycling via Home Assistant (8 min at 11 kW / 7 min at 0)* — could not have worked in principle. The capacity tariff is set from the quarter-hour *average*: 8/15 × 11.08 kW = 5.91 kW, identical to running 8.6 A continuously. No saving, only contactor wear and unreliable resume behaviour. Retired.
- *Capping the car's own charge current to 8 A* — puts the limit in the wrong place. It follows the car to every public charger too, which works against objective 3 (fast public AC charging). The cap belongs in the charger, not the car.
- *The Ohme "special tariff" workaround* (0.28 €/kWh normally, spiking 18:00–21:00) — encoded a price policy as a fake tariff. Ohme plans a session in advance against a kWh target with no reliable link to actual battery SoC; plugging in at 18:15, inside the "expensive" window, made it defer rather than charge. Set an explicit charge-by time instead.

## The fix: one number governs (almost) everything

Ohme's load balancing caps *total* current through the monitored point, not just the car, so:

**peak (kW) ≈ LOAD LIMIT (A) × 3 × 230 V**, once all three phases are correctly monitored.

Annual capacity-tariff cost is linear — €53.39/kW/yr excl. VAT (≈€64.6/kW/yr incl.) above the 2.5 kW minimum, with no cliff or threshold to dodge. So the table below gives the *absolute* annual cost at each ceiling, not a cost "extra above baseline" — that framing doesn't hold once load balancing is actually capping total draw, since the ceiling then governs the peak directly regardless of what the rest of the house is doing:

| LOAD LIMIT | Total ceiling | Annual capacity cost (from 2.5 kW floor, incl. VAT) | Car gets, house quiet | Time for 70% top-up |
|---|---|---|---|---|
| 8 A | 5.52 kW | ~€195/yr | 4.55 kW | ~15.4 h |
| 9 A | 6.21 kW | ~€239/yr | 5.24 kW | ~13.3 h |
| **10 A — recommended** | **6.90 kW** | **~€284/yr** | **5.93 kW** | **~11.8 h** |
| 11 A | 7.59 kW | ~€329/yr | 6.62 kW | ~10.6 h |
| 12 A | 8.28 kW | ~€373/yr | 7.31 kW | ~9.6 h |
| 32 A (current setting) | 22.16 kW | n/a — never a real ceiling | 11.0 kW (car-limited) | ~6.9 h, no protection |

**Recommendation stands: LOAD LIMIT = 10 A per phase, MAX CHARGE CURRENT stays at 16 A** so the load limit is the actual governor. Modelled against a realistic 17:30–07:00 evening with ~2.5 hours lost/reduced to cooking: ~68 kWh at the meter ≈ 61 kWh to the battery ≈ 70% of gross capacity — meets the target with margin, self-managing (full speed when the house is quiet, throttled during dinner, back up after), no scheduling or SoC visibility required.

**Fallback:** if LOAD LIMIT can't go that low, or the CT clamps prove unreliable, cap MAX CHARGE CURRENT at 8 A instead — cruder, no adaptive behaviour, but bounded by physics rather than by a sensor that might be blind.

## How much capacity headroom is reasonable?

There's no natural wall to stay under — the tariff is a straight €64.6/kW/yr, at any level, so it's a budget dial rather than a threshold to dodge. A few anchors to set that dial by:

- **Pre-EV-charging household baseline:** ~3.1 kW (rolling 12-month average, Mar 2025–Feb 2026, before routine home EV charging — see Fact Sheet). That's roughly what the house draws on its own.
- **Current "new normal" once EV charging is routine:** monthly peaks of 4.6–5.4 kW even under the old, unmanaged single-phase setup, most months (see Fact Sheet). That's not a fault — it's what a single EV-charging session naturally costs, once it's the highest quarter-hour of the month.
- **What dropping gas is worth, in headroom terms:** the Heating Plan estimates €100–150/yr in gas standing/connection charges disappearing on full electrification. At €64.6/kW/yr, that funds roughly **1.5–2.3 kW of extra permanent ceiling** — cost-neutral against the current gas connection fee alone, before counting anything else.
- **The real risk isn't the ceiling, it's coincidence.** Every outsized peak in the data so far — August's car-plus-cooking spike, July's isolated high-power event — came from two things landing in the same 15-minute window, not from the ceiling being "too high." As air2air and later air2water (with its 3–9 kW backup element) come online, that risk grows, especially since backup-element activation and a fortnightly big EV charge both skew toward cold, dark evenings. Sequencing loads through Home Assistant (see below) protects against this at any ceiling; raising the ceiling alone doesn't.

No need to lock in one number today. Treat it as: pick a LOAD LIMIT with sensible margin now (10 A / 6.9 kW), revisit as the heat pump sizing firms up, and lean on load sequencing — not on raising the ceiling — to absorb new flexible loads without recreating August.

## Capacity tariff — the mechanics, for reference

- Fluvius records the highest quarter-hour *average* import each calendar month. The annual charge = average of the 12 monthly peaks (minimum 2.5 kW) × rate.
- 2026 Flanders reference rate: **~€53.39/kW/yr excl. VAT** (regional range ~€49–57); **≈ €64.6/kW/yr incl. VAT**.
- A bad month is only ever 1/12th as costly as it feels — it only adds that fraction of its excess to the rolling 12-month average, and fades out again if not repeated.
- Corollary: any charging done before a tariff month closes, at or below the peak already reached that month, costs nothing extra.
- **Current data:** see Fact Sheet → Measured Peak History for the actual monthly figures and rolling averages — kept there so this doc doesn't go stale as new months arrive.

## CT clamps — verify before trusting any of this

The app currently shows one aggregate "CT CLAMP READING." On a three-phase board this should ideally be per-phase; if only one clamp is fitted, or the reading doesn't see all three phases, an unbalanced load (e.g. the induction hob on a single phase) is invisible to load balancing regardless of the LOAD LIMIT setting.

**Test it directly:** watch the CT Clamp Reading while switching a known ~2 kW load on and off (oven, kettle). Expect roughly an 8.7 A step change. Repeat for loads believed to be on different circuits. If some loads move the reading and others don't, there's a blind phase.

This also matters for solar (below): the clamps need to be positioned to read **net grid import**, not gross house consumption, or the car will be throttled against generation it can't see.

## After solar goes live (installed Wed 26 Aug) — daytime charging

If the CT clamps are correctly positioned, **no separate mechanism is needed**: LOAD LIMIT then governs *grid import*, not raw car draw, and solar generation simply doesn't count against it. Example: with a 10 A / 6.9 kW LOAD LIMIT and 2 kW of solar running, the car can draw ~8.5 kW while grid import stays at 6.9 kW.

This means the daytime solar-matching objective and the evening capacity-tariff fix are **the same setting**, resolved by one correct installation choice — clamp placement — not two separate configurations.

Ohme's own branded "Solar Boost" / "Solar Only" modes are a separate, optional layer on top:

- Require the CT clamp (same one as above) to be fitted, app version **2.10.2 or later**, and Ohme's own eligibility check — which by their own support docs can take "a few charge sessions" of live solar data before the option even appears in Settings → Charging settings → Solar charging. **Don't expect it the day the panels go live** — allow a week or two of sunny sessions first.
- No pairing to the EcoFlow inverter/battery is required — Ohme's clamp reads current directly and is agnostic to the generation source.
- On three-phase chargers specifically, Ohme's documented solar thresholds are higher and the grid-assisted blend mode offered to single-phase units may not be available — so treat correctly-placed CT clamps + LOAD LIMIT as the mechanism doing the real work, and Solar Boost as a bonus if and when it appears.

Rough value of getting clamp placement right: solar surplus over baseline household draw, March–October, is roughly 2,776 kWh/yr; capturing 25–40% of that into the car instead of exporting it is worth **~€170–280/yr** — larger than the capacity-tariff saving, worth stating plainly to whoever positions the clamps.

## Home Assistant's realistic role

**No live/local control of Ohme charging current exists.** The official integration is cloud-polling (~30 s) and exposes: charge mode (Smart / Max / Paused), target %, target time, price cap, a solar-boost switch, and a *read-only* current sensor. There is no "set current to X A" entity anywhere — current control happens only inside the Ohme app/installer settings, or automatically via the charger's own CT-based load-balancing loop.

**Live vehicle SoC is not realistically available.** The community XPeng integration is a small, largely unmaintained project requiring one's own Enode production credentials, and the public proxy services that filled that gap have hit their caps. Not worth pursuing now — the plan above doesn't depend on it, since "start early, take whatever headroom exists, stop when full or at 07:00" is correct whether the car arrives at 10% or 40%.

**What Home Assistant can usefully do — and why it matters more as electrification proceeds** (see "How much capacity headroom is reasonable?" above — coincidence, not ceiling size, is the real risk):

- Read the Siconia T211 smart meter via its P1 port (e.g. HomeWizard P1 / Slimmelezer) for live total household kW and a running quarter-hour average — local, real-time, the actual ground truth. (P1 port currently not delivering a signal — see Fact Sheet open items; test scheduled 26 Aug.)
- Keep appliance schedules (dishwasher, washing machine, dryer) clear of the car's charging window rather than trying to co-optimise live — disjoint windows, not simultaneous throttling. The Ohme's own load-balancing floor is 6 A/phase, so once headroom drops below that it pauses the car outright rather than trimming it.
- Set Ohme's charge mode / target time for the fortnightly "full by 7am" event (ensure target time = 07:00, plug in as early as possible after arrival).
- Act as a backstop only: pause the Ohme session if the running quarter-hour projection is heading over budget, accepting the ~30 s cloud round-trip. A safety net, not the primary control loop — that's the Ohme's own local CT loop, once correctly configured.
- Longer term, sequence the car against the eventual air2water backup element too, once that's installed — same principle, bigger stakes.

## Reference: Amps ↔ kW ↔ kWh

Different sources — the car's menu, the Ohme app, electricians, public charge points — quote "amps" against single-phase, three-phase, or leave it ambiguous, which is the main source of confusion in this whole topic. Two things to always pin down: (1) is a given amp figure *per phase* or for the whole circuit, and (2) how many phases.

**Single-phase (230 V)** — `kW = 230 × A ÷ 1000`

| Current | Power | Time for a 70% top-up (~68 kWh at meter) |
|---|---|---|
| 6 A | 1.38 kW | ~49 h |
| 8 A | 1.84 kW | ~37 h |
| 10 A | 2.30 kW | ~30 h |
| 13 A (typical "granny cable") | 2.99 kW | ~23 h |
| 16 A (old home setup) | 3.68 kW | ~18.5 h |
| 20 A | 4.60 kW | ~15 h |
| 32 A | 7.36 kW | ~9 h |

**Three-phase (230 V per phase)** — `kW = 3 × 230 × A ÷ 1000` (A is the *per-phase* figure)

| Current (per phase) | Power | Time for a 70% top-up (~68 kWh at meter) | Note |
|---|---|---|---|
| 6 A (Ohme/car minimum) | 4.14 kW | ~16.5 h | |
| 7 A | 4.83 kW | ~14.1 h | |
| 8 A | 5.52 kW | ~12.3 h | |
| 9 A | 6.21 kW | ~11.0 h | |
| **10 A — recommended LOAD LIMIT** | **6.90 kW** | **~9.9 h** | fits 17:30–07:00 with cooking allowed for |
| 12 A | 8.28 kW | ~8.2 h | |
| 16 A (car's OBC ceiling) | 11.04 kW | ~6.2 h | XPeng G6 On-Board Charger maxes out here — more current from the charger or grid buys nothing beyond this |
| 32 A (Ohme's current setting) | 22.16 kW | n/a | never reachable — car is hard-capped at 16 A/11 kW by its own OBC, so this setting has given zero protection since the 3F+N upgrade |

**Fixed reference points for this house:**

- Old single-phase setup: 16 A → 3.68 kW — the "3.7 kW" previously experienced.
- XPeng G6 On-Board Charger (OBC) hard limit: **11 kW / 16 A three-phase** — no benefit from more current regardless of charger or grid capacity.
- 70% top-up ≈ **61 kWh to the battery** (87.5 kWh gross pack) ≈ **68 kWh at the meter**, assuming ~90% AC charging efficiency.

## Questions for the Ohme electrician

*(He owes us this — never returned to the installer portal after the 3F+N upgrade. Top priority; some steps already underway.)*

1. How many CT clamps are fitted — one or three? On which conductors, positioned where (meter tails vs. board)?
2. Are the clamps positioned to read net grid import, or gross house consumption? (Matters both for the capacity-tariff fix and for post-solar daytime charging.)
3. Please change LOAD LIMIT from 32 A to **10 A per phase**.
4. Is LOAD LIMIT a per-phase figure or a total? What's the lowest settable value?
5. Confirm MAX CHARGE CURRENT stays at 16 A per phase, load balancing stays on.
6. Confirm nothing else in the configuration is still set for single-phase.
7. What is the actual connection/main fuse rating (3×40 A? 3×63 A?) — also relevant for the solar installer.
8. Screenshot of the final settings once changed, for our records.

*(Requires "Enable Config Requests" switched on in the app before he can make remote changes.)*

## Questions / notes for the solar electrician (Wed 26 Aug)

Printable bilingual version: `Solar checklist.pdf`, same folder.

1. Query the Fact Sheet's noted "1-phase CT" EcoFlow energy meter spec on the 3F+N PowerOcean system — single-phase metering on an unbalanced three-phase supply will mis-track; get this right on day one.
2. Ensure the EcoFlow's CTs and the Ohme's CTs are both positioned upstream of everything, and not interfering with each other.
3. Ask about leaving the Siconia T211's P1 port accessible with a cable route to wherever Home Assistant will live — cheap while they're on site, and it's the only local, real-time view of total grid draw.
4. Ask which phases the major kitchen circuits (hob, oven, dryer) are on — doesn't change the capacity tariff itself (that's total kW) but affects how often the Ohme throttles the car if the clamps are uneven or one phase is disproportionately loaded.
5. EcoFlow charge/discharge strategy — decision already taken, parked separately, not part of this note.

## Open items

- Confirm whether LOAD LIMIT will accept 10 A, and the practical minimum.
- Run the CT-clamp blind-spot test once changes are made.
- Re-check the car's own AC amp limit — reset to maximum now that the cap has moved to the charger, so public/supermarket AC charging (objective 3) isn't needlessly restricted.
- Revisit XPeng SoC visibility later if a maintained integration or OBD-based option appears — not needed for the current plan.
- Revisit the target LOAD LIMIT once heat pump sizing (air2air, then air2water) is further along — see "How much capacity headroom is reasonable?" above.

## Current plan

Set the Ohme's LOAD LIMIT to **10 A per phase** (leave MAX CHARGE CURRENT at 16 A, load balancing on) — top priority, steps already underway. This single change is expected to solve the capacity-tariff problem, the cooking-clash problem, and — once CT clamp placement is confirmed correct — the post-solar daytime-charging objective, all at once, with no Home Assistant scripting and no dependence on car SoC visibility. Retire the 15-minute on/off duty-cycling automation and the fake-tariff workaround; neither can outperform a correctly-set LOAD LIMIT. Reset the car's own amp limit to maximum so it no longer restricts public charging. Verify CT clamp coverage and placement empirically once the Ohme electrician has made the change and the solar panels are live. Don't chase a single "correct" capacity ceiling — treat it as a budget that grows mainly by dropping gas, and rely on load sequencing (not a higher ceiling) to keep new loads from recreating August's coincidence.
