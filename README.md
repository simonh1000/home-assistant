# Home Assistant Automations: 6kW Capacity Guardian

This system manages EV charging and house load to ensure an approx **6.0 kW** monthly average peak in Flanders, Belgium.

The car currently is set to limit charging to 8A

## 🧠 The Logic (15-Min Window)

To avoid high capacity tariffs, we ensure the 15-minute average stays below 6kW:

- **Active Defense:** We monitor for **5 minutes above 6.5kW**.
- **Automatic Response:** If triggered, the EV charger is paused immediately.
- **Recovery:** Charging resumes once the load is low (< 4kW) or after the dinner peak.

---

## 📂 Core Automations

### 1. [ev-capacity-guardian.yaml](src/automations/ev-capacity-guardian.yaml)

- **Power Guard:** Pauses EV if house draw > 6.0 kW for 30 seconds (`ev_guardian_state: yielding`).
- **Dinner Lockout:** Automatically pauses EV daily from **18:15 to 20:00** (unless overridden by `ev_cooking_over`).
- **Smart Resume:** Moves to `cooldown` state after 2 minutes under 500W, and resumes charging once quiet for 10 minutes total or via the 22:30 safety net.

### 2. [ev-cooking-over.yaml](src/automations/ev-cooking-over.yaml)

- **Manual Resume:** Resumes EV charging immediately when the "Cooking Over" button is pressed, ending any dinner lockout or yielding state.

### 3. [ev-approval-notifier.yaml](src/automations/ev-approval-notifier.yaml)

- **Reminder:** If Ohme is pending approval at 22:30, send reminder to both phones, with approve button.

### 4. [ev-approve.yaml](src/automations/ev-approve.yaml)

- **Button Handler:** Processes the "Approve" button click from "reminder" notification to start the charge.

### 5. [peak-alert.yaml](src/automations/peak-alert.yaml)

- **Awareness Only:** Sends a warning at **6.0 kW** (sustained for 2 mins). It does not take action; it just keeps you informed.

### 6. [ev-charge-completed.yaml](src/automations/ev-charge-completed.yaml)

- **Charge Completion:** Sends a notification to both phones when the Ohme charger finishes charging outside of Guardian pauses.

### 7. [ecoflow-battery-lock.yaml](src/automations/ecoflow-battery-lock.yaml) & [ecoflow-battery-unlock.yaml](src/automations/ecoflow-battery-unlock.yaml)

- **Battery Protection:** When the Ohme starts charging, hands the EcoFlow battery over to Modbus control and pins charge/discharge at 0 W (via [ecoflow_lock_battery.yaml](src/scripts/ecoflow_lock_battery.yaml)) so the car can't drain stored battery energy — it only pulls from solar/grid. Reverts to normal self-consumption control (via [ecoflow_unlock_battery.yaml](src/scripts/ecoflow_unlock_battery.yaml)) once charging stops.
- **Status:** untested — depends on the installer confirming Modbus control mode is active on the inverter (see [TODO](#-todo)). Register map is documented in [ecoflow.yaml](src/modbus/ecoflow.yaml).

---

## 🏠 Dashboard Widget

The system now includes a managed dashboard **Capacity Guardian** defined in `src/ui-lovelace.yaml` and is automatically deployed to Home Assistant alongside your automations and scripts.

To use it, ensure your Home Assistant is in **YAML Mode** for dashboards (this is handled by the included `configuration.yaml`).

The dashboard includes:

1.  **Guardian Status**: Real-time view of the `Idle`, `Yielding`, or `Cooldown` state.
2.  **Cooking Over Button**: Manual override to resume charging.
3.  **State explanation**: A markdown card detailing what each state means.

---

## 📜 Helper Scripts

### [notify_both_phones.yaml](src/scripts/notify_both_phones.yaml)

- A centralized script used by other automations to send alerts to both Pixel 10 and Pixel 8 simultaneously.

### [notify_simon.yaml](src/scripts/notify_simon.yaml) & [notify_liesbeth.yaml](src/scripts/notify_liesbeth.yaml)

- Targeted notification scripts for Pixel 10 (Simon) and Pixel 8 (Liesbeth) individually.

### [ecoflow_lock_battery.yaml](src/scripts/ecoflow_lock_battery.yaml) & [ecoflow_unlock_battery.yaml](src/scripts/ecoflow_unlock_battery.yaml)

- Modbus writes that lock/unlock the EcoFlow battery's charge/discharge, driven by the ecoflow-battery-lock/unlock automations above. `ecoflow_lock_battery` also loops a heartbeat write every 45s for as long as the car is charging (required by the inverter at least every 60s to keep the override active).

---

## ⚙️ Configuration & Deployment

### File Structure

- **Automations:** Files in `src/automations/*.yaml` are copied as-is to `dist/src/automations/`. `configuration.yaml` picks them up with `!include_dir_list src/automations`, so each file must contain a single automation (with a stable `id:` field).
- **Scripts:** Files in `src/scripts/*.yaml` are copied as-is to `dist/src/scripts/`. `configuration.yaml` picks them up with `!include_dir_merge_named src/scripts`, so each file's content must be nested under a single top-level key matching the script's id (e.g. `notify_simon:`).
- **Helpers & Config:** `src/helpers.yaml` and `src/configuration.yaml` are copied to `dist/`.
- **Web Assets:** Files in `src/www/` are copied to `dist/www/`.

Because HA resolves `!include_dir_*` paths relative to its config root, the deployed HA config directory needs a `src/automations/` and `src/scripts/` folder of its own — `combine.py --deploy` uploads `dist/src/` (via `rsync --delete`, so files removed locally are also removed on the HA host) alongside the usual flat files.

### 🚀 How to Update & Upload

1.  **Consolidate:** Run `./combine.py` to generate output in `dist/`.
2.  **Upload:** Run `./combine.py --deploy` (requires `.env` setup).
    - **Versioning:** The script uses the `VERSION` file in the root.
    - You must **manually** increment the version in the `VERSION` file before merging a PR to `main` (the CI check enforces this).
    - Alternatively, run `./combine.py --deploy -v 1.2.0` to update the file and deploy in one go.
    - This will upload automations, scripts, helpers, configuration, and web assets.
3.  **Reload:** Go to HA -> **Settings -> Tools -> YAML** -> click **Automations** and **Scripts**.
    - _Note:_ If `HA_DEPLOY` token is set in `.env`, the script will automatically trigger a reload and update the version state.

---

## 📝 TODO

* [ ] Daily challenge: sum of energy produced - background use during sunny hours - battery capacity
* [ ] Turn of battery discharge when car charging — drafted via Modbus (`ecoflow-battery-lock.yaml`/`ecoflow-battery-unlock.yaml`), untested pending installer confirming Modbus control mode
* [ ] Get the car to take up the remaining capacity
* [ ] Prevent the car consuming energy from the battery (either use enhanced mode and my poersonal password, or modbus) — see above, drafted not tested
* [ ] Catch case when charging stops unexpectedly and not at 100% (not clear how we can know that)?
* [ ] Yield after slightly longer spike (perhaps linked to level) so coffee does not affect it?
* [ ] Follow up with installer — EcoFlow Modbus returns "Illegal Data Address" on every register despite him saying he'd enabled it

### 📱 Installer follow-up (EcoFlow Modbus)

**Confirmed working:** Step 1 (network/cable) is done — port 502 on 192.168.0.165 is open, accepts connections, and the inverter responds with valid Modbus TCP frames. **Not confirmed:** Step 2 — every register read (any address, function code 03 or 04) comes back "Illegal Data Address", including the most basic one (Protocol Version), which points at Modbus control mode not being active in the EcoFlow Pro app.

**SMS to send (NL):**

> Hoi, met Simon. De Modbus-poort van de EcoFlow staat open en de verbinding werkt, maar hij geeft op elk register "Illegal Data Address" terug — lijkt erop dat Modbus-besturing zelf niet actief staat in de EcoFlow Pro app. Zou je kunnen checken of die nog aanstaat voor deze omvormer? Bedankt, bel gerust terug wanneer het past!

**If he calls back — talking points:**

NL:
- Staat "Modbus control mode" nog actief aan voor deze omvormer in de EcoFlow Pro app? (Kan uitgeschakeld zijn, of teruggevallen naar normale modus.)
- Welk exact model is het (PowerOcean single-phase / three-phase / Plus, of OCEAN2)? Het register-overzicht verschilt per model.
- Welke firmwareversie draait erop?
- Moet er om de 60 seconden een "heartbeat"-signaal teruggestuurd worden, en beïnvloedt dat ook het uitlezen van data, of enkel het aansturen/schrijven?
- Is er nog een andere app of tool tegelijk via Modbus verbonden op hetzelfde toestel? (mogelijk conflict)
- Welk slave/unit-ID gebruikt hij? (wij gaan momenteel uit van 1)

EN:
- Is "Modbus control mode" still switched on for this inverter in the EcoFlow Pro app? (It may have been disabled, or reverted to normal mode.)
- Exact model of the device (PowerOcean single-phase / three-phase / Plus, or OCEAN2)? The register map differs by model.
- What firmware version is it running?
- Does a "heartbeat" signal need to be sent back every 60 seconds, and does that gate reads too, or only writes/control?
- Is any other app or tool connected via Modbus to the same device at the same time? (possible conflict)
- What slave/unit ID is configured? (we're currently assuming 1)
