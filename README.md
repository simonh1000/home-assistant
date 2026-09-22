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

### 2. [ev-approval-notifier.yaml](src/automations/ev-approval-notifier.yaml)
*   **Security Gate:** Sends an actionable notification to both phones when the Ohme charger is "Pending Approval."
*   **Reminder:** Sends a follow-up alert at 22:30 if the charge is still waiting.

### 3. [ev-approve.yaml](src/automations/ev-approve.yaml)
*   **Button Handler:** Processes the "Approve" button click from your mobile notification to start the charge.

### 4. [peak-alert.yaml](src/automations/peak-alert.yaml)
*   **Awareness Only:** Sends a warning at **6.0 kW** (sustained for 2 mins). It does not take action; it just keeps you informed.

### 5. [ev-charge-completed.yaml](src/automations/ev-charge-completed.yaml)

- **Charge Completion:** Sends a notification to both phones when the Ohme charger finishes charging outside of Guardian pauses.

### 6. [ev-cooking-over.yaml](src/automations/ev-cooking-over.yaml)

- **Manual Resume:** Resumes EV charging immediately when the "Cooking Over" button is pressed, ending any dinner lockout or yielding state.

---

## 🏠 Dashboard Widget

The system now includes a managed dashboard defined in `src/ui-lovelace.yaml`. It is automatically deployed to Home Assistant alongside your automations and scripts.

To use it, ensure your Home Assistant is in **YAML Mode** for dashboards (this is handled by the included `configuration.yaml`).

The dashboard includes:
1.  **Guardian Status**: Real-time view of the `Idle`, `Yielding`, or `Cooldown` state.
2.  **Cooking Over Button**: Manual override to resume charging.
3.  **State explanation**: A markdown card detailing what each state means.

---

## 📜 Helper Scripts

### [notify_both_phones.yaml](src/scripts/notify_both_phones.yaml)
*   A centralized script used by other automations to send alerts to both Pixel 10 and Pixel 8 simultaneously.

### [notify_simon.yaml](src/scripts/notify_simon.yaml) & [notify_liesbeth.yaml](src/scripts/notify_liesbeth.yaml)
*   Targeted notification scripts for Pixel 10 (Simon) and Pixel 8 (Liesbeth) individually.

---

## ⚙️ Configuration & Deployment

### File Structure
*   **Automations:** Files in `src/automations/*.yaml` are combined into `dist/automations.yaml`.
*   **Scripts:** Files in `src/scripts/*.yaml` are combined into `dist/scripts.yaml`.
*   **Helpers & Config:** `src/helpers.yaml` and `src/configuration.yaml` are copied to `dist/`.
*   **Web Assets:** Files in `src/www/` are copied to `dist/www/`.

### 🚀 How to Update & Upload

1.  **Consolidate:** Run `./combine.py` to generate output in `dist/`.
2.  **Upload:** Run `./combine.py --deploy` (requires `.env` setup). 
    - **Versioning:** The script maintains a `VERSION` file in the root. 
    - If you run with just `--deploy`, it **auto-increments** the patch version (e.g., `1.0.0` → `1.0.1`).
    - To set a specific version, use `./combine.py --deploy -v 1.2.0`.
    - This will upload automations, scripts, helpers, configuration, and web assets.
3.  **Reload:** Go to HA -> **Settings -> Tools -> YAML** -> click **Automations** and **Scripts**.
    - *Note:* If `HA_DEPLOY` token is set in `.env`, the script will automatically trigger a reload and update the version state.

---

## 📝 TODO

- [x] Add `/src` directory
- [x] **Automate Reload**: Add support for Home Assistant API to automatically trigger `automation.reload` and `script.reload` after deployment. Requires a Long-Lived Access Token stored as `HA_DEPLOY` in `.env`.
- [x] **Notification when charging complete**
- [ ] **Button to say 'cooking over'**
* [ ] Catch case when charging stops unexpectedly and not at 100% (not clear how we can know that)?
* [ ] Yield after slightly longer spike (perhaps linked to level) so coffee does not affect it?
