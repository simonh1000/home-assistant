# Home Assistant Automations: 6kW Capacity Guardian

This system is designed to keep your 15-minute average power consumption in Flanders, Belgium, below **6.0 kW**.

## 🧠 The Logic (15-Min Window)
The Flemish capacity tariff is based on the highest 15-minute average in a month. To stay below 6kW:
*   **Buffer:** We monitor for **5 minutes above 6.5kW**. 
*   **Reaction:** If that threshold is hit, we pause the EV charger immediately. 
*   **Result:** By cutting 11kW of load for the remaining 10 minutes of the window, we ensure the 15-minute average stays safely below the 6kW target.

---

## 📂 Simplified Structure
We have consolidated everything into a single "Guardian" to eliminate conflicting logic.

### 1. ev-capacity-guardian.yaml (Master Control)
*   **Power Guard:** Pauses EV if house draw > 6.5 kW for 5 minutes.
*   **Dinner Lockout:** Automatically pauses EV daily from **18:15 to 20:00**.
*   **Smart Resume:** Resumes charging when load drops below 4.0kW for 10 minutes, or at 06:00.

### 2. peak-alert.yaml (Awareness)
*   **Notification Only:** Warns you at **6.0 kW** (after 2 minutes) so you can manually check appliances if needed. No automated actions.

---

## ⚙️ Global State
To keep the system reliable, we use minimal state:
1.  **Input:** `sensor.p1_meter_active_power` (Your digital meter).
2.  **Output:** `select.ohme_home_pro_delta_11kw_charge_mode` (The Ohme mode).
3.  **Conflict Prevention:** Only ONE script is responsible for changing the charger mode.

---

## 🚀 How to Update & Upload
1.  **Consolidate:** Run `./combine.py` in this folder.
2.  **Upload:** Run `./combine.py --deploy` (requires `.env` setup).
3.  **Reload:** Go to HA -> **Settings -> Tools -> YAML** -> click **Automations**.
