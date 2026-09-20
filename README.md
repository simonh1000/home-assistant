# Home Assistant Automations: Energy & EV Management

These automations keep your 15-minute average peaks below **6.0 kW** in Flanders, Belgium.

---

## 🎛️ Dashboard Switch (Manual Setup Required)
To make the "Tuesday Night Override" work, you must create **one** Helper in Home Assistant (**Settings -> Devices -> Helpers**):

1.  **Create Toggle:** Name it `"EV Deadline Charge Override"`
    *   **Action:** Click **+ CREATE HELPER** -> **Toggle**.
    *   **Verify Entity ID:** Ensure it is exactly `input_boolean.ev_deadline_charge_active`.

**How to use it:**
*   **Flip it ON:** The car starts its "Ready by 7am" session and guards tighten.
*   **Flip it OFF:** The car returns to normal mode immediately.
*   **Automatic:** It will turn itself OFF every Wednesday morning at 07:15.

---

## 📂 Scripts Summary

### 1. peak-alert.yaml (Active Protection)
*   **Logic:** Pauses EV if house draw > 6.5 kW for 5 minutes.

### 2. ev-lockout.yaml (Scheduled)
*   **Logic:** Pauses EV daily during the 18:30 - 20:45 window. Resumes at 06:00.

### 3. ev-safety.yaml (Emergency Circuit Breaker)
*   **Logic:** Auto-pauses EV if total house draw > 9 kW for 8 minutes.

### 4. ev-deadline-activate.yaml / revert.yaml
*   **Logic:** Triggered by the dashboard Toggle. Handles the 07:00 deadline sessions.

---

## 🚀 How to Update & Upload
1.  **Consolidate:** Run `./combine.sh` in this folder.
2.  **Upload:** Drag `automations.yaml` to your HA Green `/config/` folder.
3.  **Reload:** Go to HA -> **Settings -> Tools -> YAML** -> click **Automations**.

```sh
./combine.sh --deploy
```

---

## ☀️ Tomorrow's Checklist
1.  **Helper:** Ensure the Toggle exists with the correct ID.
2.  **Sync:** Run `./combine.sh`.
3.  **Reload:** Reload Automations in the HA UI.
4.  **Test:** Flip the Toggle **ON**. Check if you get a notification on your Pixel.
