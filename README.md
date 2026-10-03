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
- **Dinner Lockout:** Automatically pauses EV daily from **18:15 to 20:15** (`ev_guardian_state: cooking`). If a load pause (`yielding`/`cooldown`) is already running at 18:15 it hands over to `cooking`; at 20:15 `cooking` returns to `idle` and a paused EV resumes.
- **Smart Resume:** Moves to `cooldown` state after 2 minutes under 500W, and resumes charging once quiet for 10 minutes total or via the 22:30 safety net.

### 2. [ev-cooking-over-button-handler.yaml](src/automations/ev-cooking-over-button-handler.yaml)

- **Manual Resume:** Resumes EV charging immediately when the "Done Cooking" button is pressed, transitioning `cooking` state to `idle`.

### 3. [ev-approval-notifier.yaml](src/automations/ev-approval-notifier.yaml)

- **Reminder:** If Ohme is pending approval at 22:30, send reminder to both phones, with approve button.

### 4. [ev-approve.yaml](src/automations/ev-approve.yaml)

- **Button Handler:** Processes the "Approve" button click from "reminder" notification to start the charge.

### 5. [peak-alert.yaml](src/automations/peak-alert.yaml)

- **Awareness Only:** Sends a warning at **6.0 kW** (sustained for 2 mins). It does not take action; it just keeps you informed.

### 6. [ev-charge-completed.yaml](src/automations/ev-charge-completed.yaml)

- **Charge Completion:** Sends a notification to both phones when the Ohme charger finishes charging outside of Guardian pauses.

### 7. [ecoflow-battery-lock.yaml](src/automations/ecoflow-battery-lock.yaml) & [ecoflow-battery-unlock.yaml](src/automations/ecoflow-battery-unlock.yaml)

- **Battery Protection:** When the Ohme starts charging, switches the EcoFlow integration (MaxGrmm/EF-PowerOcean-TcpModbus) to **Hold battery** with Modbus Control on (via [ecoflow_lock_battery.yaml](src/scripts/ecoflow_lock_battery.yaml)) so the car can't drain stored battery energy — it only pulls from solar/grid. Reverts to normal self-consumption control (via [ecoflow_unlock_battery.yaml](src/scripts/ecoflow_unlock_battery.yaml): Battery Mode back to Automatic, Modbus Control off) once charging stops.
- **Status:** untested. Uses `switch.garage_ecoflow_powerocean_modbus_control` and `select.ecoflow_powerocean_battery_mode` — check these entity IDs exist in your install (see [TODO](#-todo)).

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

### [notify_simon.yaml](src/scripts/notify_simon.yaml) & [notify_partner.yaml](src/scripts/notify_partner.yaml)

- Targeted notification scripts for Pixel 10 (Simon) and Pixel 8 (Partner) individually.

### [ecoflow_lock_battery.yaml](src/scripts/ecoflow_lock_battery.yaml) & [ecoflow_unlock_battery.yaml](src/scripts/ecoflow_unlock_battery.yaml)

- Set the EcoFlow integration's Battery Mode (Hold battery / Automatic) and Modbus Control switch, driven by the ecoflow-battery-lock/unlock automations above. The integration sends the inverter heartbeat itself.

---

## ⚙️ Configuration & Deployment

### File Structure

- **Automations:** Files in `src/automations/*.yaml` are copied as-is to `dist/src/automations/`. `configuration.yaml` picks them up with `!include_dir_list src/automations`, so each file must contain a single automation (with a stable `id:` field).
- **Scripts:** Files in `src/scripts/*.yaml` are copied as-is to `dist/src/scripts/`. `configuration.yaml` picks them up with `!include_dir_merge_named src/scripts`, so each file's content must be nested under a single top-level key matching the script's id (e.g. `notify_simon:`).
- **Helpers & Config:** Files in `src/helpers/` are copied to `dist/helpers/`, and `src/configuration.yaml` to `dist/`.
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

* [x] Daily challenge: sum of energy produced - background use during sunny hours - battery capacity
  * [x] Update surplus prediction throughout the day
  * [x] Get more regular battery updates - modbus

* [ ] Turn of battery discharge when car charging — drafted via the EcoFlow integration's Battery Mode (`ecoflow-battery-lock.yaml`/`ecoflow-battery-unlock.yaml`), untested
  * [ ] Prevent the car consuming energy from the battery — see above, drafted not tested

* [ ] Get the car to take up the remaining capacity

* [ ] Catch case when charging stops unexpectedly and not at 100% (not clear how we can know that)?

* [ ] Yield after slightly longer spike (perhaps linked to level) so coffee does not affect it?
