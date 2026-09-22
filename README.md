# Home Assistant Automations: 6kW Capacity Guardian

This system manages EV charging and house load to ensure an approx **6.0 kW** monthly average peak in Flanders, Belgium.

The car currently is set to limit charging to 8A

## 🧠 The Logic (15-Min Window)
To avoid high capacity tariffs, we ensure the 15-minute average stays below 6kW:
*   **Active Defense:** We monitor for **5 minutes above 6.5kW**.
*   **Automatic Response:** If triggered, the EV charger is paused immediately.
*   **Recovery:** Charging resumes once the load is low (< 4kW) or after the dinner peak.

---

## 📂 Core Automations

### 1. [ev-capacity-guardian.yaml](ev-capacity-guardian.yaml)
*   **Power Guard:** Pauses EV if house draw > 6.5 kW for 5 minutes.
*   **Dinner Lockout:** Automatically pauses EV daily from **18:15 to 20:00**.
*   **Smart Resume:** Resumes charging when load drops below 4.0kW for 10 minutes, or at 06:00.

### 2. [ev-approval-notifier.yaml](ev-approval-notifier.yaml)
*   **Security Gate:** Sends an actionable notification to both phones when the Ohme charger is "Pending Approval."
*   **Reminder:** Sends a follow-up alert at 22:30 if the charge is still waiting.

### 3. [ev-approve.yaml](ev-approve.yaml)
*   **Button Handler:** Processes the "Approve" button click from your mobile notification to start the charge.

### 4. [peak-alert.yaml](peak-alert.yaml)
*   **Awareness Only:** Sends a warning at **6.0 kW** (sustained for 2 mins). It does not take action; it just keeps you informed.

### 5. [ev-charge-completed.yaml](ev-charge-completed.yaml)
*   **Charge Completion:** Sends a notification to both phones when the Ohme charger finishes charging outside of Guardian pauses.

---

## 📜 Helper Scripts

### [notify_both_phones.script.yaml](notify_both_phones.script.yaml)
*   A centralized script used by other automations to send alerts to both Pixel 10 and Pixel 8 simultaneously.

### [notify_simon.script.yaml](notify_simon.script.yaml) & [notify_liesbeth.script.yaml](notify_liesbeth.script.yaml)
*   Targeted notification scripts for Pixel 10 (Simon) and Pixel 8 (Liesbeth) individually.

---

## ⚙️ Configuration & Deployment

### File Structure
*   **Automations:** Files named `*.yaml` are combined into `dist/automations.yaml`.
*   **Scripts:** Files named `*.script.yaml` are combined into `dist/scripts.yaml`.
*   **Web Assets:** Local images or files for the UI should be placed in `/config/www/`.

### 🚀 How to Update & Upload

1.  **Consolidate:** Run `./combine.py` in this folder to generate output in `dist/`.
2.  **Upload:** Run `./combine.py --deploy --version-tag 1.2.3` (requires `.env` setup). 
    - *Note:* The `--version-tag` (or `-v`) is **required** when deploying.
    - This will upload `dist/automations.yaml`, `dist/scripts.yaml`, `dist/helpers.yaml`, and `dist/configuration.yaml`.
3.  **Reload:** Go to HA -> **Settings -> Tools -> YAML** -> click **Automations** and **Scripts**.
    - *Note:* If `HA_DEPLOY` token is set in `.env`, the script will automatically trigger a reload and update the version state.

---

## 📝 TODO

- [ ] Add `/src` directory
- [x] **Automate Reload**: Add support for Home Assistant API to automatically trigger `automation.reload` and `script.reload` after deployment. Requires a Long-Lived Access Token stored as `HA_DEPLOY` in `.env`.
- [x] **Notification when charging complete**
- [ ] **Button to say 'cooking over'**
*   [ ] Catch case when charging stops unexpectedly and not at 100% (not clear how we can know that)?
*   [ ] Yield after slightly longer spike (perhaps linked to level) so coffee does not affect it?
