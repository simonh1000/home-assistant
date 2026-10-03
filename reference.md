# Useful states

## Ohme

sensor.garage_ohme_car_charger_car_charger: n/a

sensor.garage_ohme_car_charger_ohme_total_energy: n/a

sensor.ohme_home_pro_delta_11kw_status: ['unplugged', 'pending_approval', 'charging', 'plugged_in', 'paused', 'finished']

sensor.ohme_home_pro_delta_11kw_current: n/a

sensor.ohme_home_pro_delta_11kw_power: n/a

sensor.ohme_home_pro_delta_11kw_voltage: n/a

sensor.ohme_home_pro_delta_11kw_vehicle_battery: n/a

sensor.ohme_home_pro_delta_11kw_charge_slots: n/a

select.ohme_home_pro_delta_11kw_charge_mode: ['smart_charge', 'max_charge', 'paused']

select.ohme_home_pro_delta_11kw_vehicle: ['XPENG G6 (2025-2025)']

## P1

sensor.p1_meter_dsmr_version: n/a

sensor.p1_meter_smart_meter_model: n/a

sensor.p1_meter_smart_meter_identifier: n/a

sensor.p1_meter_wi_fi_ssid: n/a

sensor.p1_meter_tariff: ['1', '2', '3', '4']

sensor.p1_meter_energy_import: n/a

sensor.p1_meter_energy_import_tariff_1: n/a

sensor.p1_meter_energy_import_tariff_2: n/a

sensor.p1_meter_energy_export: n/a

sensor.p1_meter_energy_export_tariff_1: n/a

sensor.p1_meter_energy_export_tariff_2: n/a

sensor.p1_meter_power: n/a

sensor.p1_meter_power_phase_1: n/a

sensor.p1_meter_power_phase_2: n/a

sensor.p1_meter_power_phase_3: n/a

sensor.p1_meter_average_demand: n/a

- Your average power consumption over a specific rolling 15-minute window (expressed in kilowatts, kW).

sensor.p1_meter_peak_demand_current_month: n/a

## Ecoflow PowerOcean 

- ModBus: https://github.com/MaxGrmm/EF-PowerOcean-TcpModbus
- MQTT/API: https://github.com/shuette42/ecoflow-energy-ha 
- Most popular but lack PowerOcean: https://github.com/tolwi/hassio-ecoflow-cloud

- Wire addresses are the protocol doc's hex offset + 40001 (e.g. SOC is 0x020E = 526 in the doc, but 40527 on the wire) — confirmed against MaxGrmm/EF-PowerOcean-TcpModbus's const.py, whose registers (grid_power=40521, battery_power=40525, battery_soc=40527, heartbeat=40608, control_command=40534, ...) all match offset+40001 exactly.

### Common to both integrations

- sensor.ecoflow_powerocean_solar_power (W)
- sensor.ecoflow_powerocean_grid_power (W)
- sensor.ecoflow_powerocean_battery_power (W)
- sensor.ecoflow_powerocean_battery_soc (%)
- sensor.ecoflow_powerocean_battery_voltage (V)
- sensor.ecoflow_powerocean_battery_current (A)
- sensor.ecoflow_powerocean_grid_frequency (Hz)
- sensor.ecoflow_powerocean_pv_string_1_power (W)
- sensor.ecoflow_powerocean_pv_string_1_voltage (V)
- sensor.ecoflow_powerocean_pv_string_1_current (A)
- sensor.ecoflow_powerocean_pv_string_2_power (W)
- sensor.ecoflow_powerocean_pv_string_2_voltage (V)
- sensor.ecoflow_powerocean_pv_string_2_current (A)

### ModBus only

- update.ecoflow_energy_update
- binary_sensor.ecoflow_powerocean_modbus_control
- binary_sensor.ecoflow_powerocean_self_powered_mode
- binary_sensor.ecoflow_powerocean_intelligent_mode
- binary_sensor.ecoflow_powerocean_system_fault
- binary_sensor.ecoflow_powerocean_system_powered_on
- sensor.ecoflow_powerocean_system_modes
- sensor.ecoflow_powerocean_house_power (W)
- sensor.ecoflow_powerocean_available_battery_charge_power (W)
- sensor.ecoflow_powerocean_available_battery_discharge_power (W)
- sensor.ecoflow_powerocean_maximum_inverter_power_dc_to_ac (W)
- sensor.ecoflow_powerocean_maximum_rectifier_power_ac_to_dc (W)
- sensor.ecoflow_powerocean_battery_nominal_capacity (Wh)
- sensor.ecoflow_powerocean_battery_temperature (°C)
- sensor.ecoflow_powerocean_grid_voltage_l1 (V)
- sensor.ecoflow_powerocean_grid_voltage_l2 (V)
- sensor.ecoflow_powerocean_grid_voltage_l3 (V)
- sensor.ecoflow_powerocean_grid_current_l1 (A)
- sensor.ecoflow_powerocean_grid_current_l2 (A)
- sensor.ecoflow_powerocean_grid_current_l3 (A)
- sensor.ecoflow_powerocean_inverter_temperature (°C)
- sensor.ecoflow_powerocean_pv_string_3_voltage (V)
- sensor.ecoflow_powerocean_pv_string_3_current (A)
- sensor.ecoflow_powerocean_pv_string_3_power (W)
- sensor.ecoflow_powerocean_maximum_feed_in_power (W)
- sensor.ecoflow_powerocean_inverter_rated_power (W)
- sensor.ecoflow_powerocean_battery_module_count
- sensor.ecoflow_powerocean_battery_1_soc (%)
- sensor.ecoflow_powerocean_battery_remaining_energy (kWh)
- sensor.ecoflow_powerocean_battery_energy_loss (kWh)
- sensor.ecoflow_powerocean_grid_mode
- sensor.ecoflow_powerocean_operating_mode
- sensor.ecoflow_powerocean_system_power_setpoint (W)
- sensor.ecoflow_powerocean_inverter_power_setpoint (W)
- sensor.ecoflow_powerocean_battery_power_setpoint (W)
- sensor.ecoflow_powerocean_active_fault_count
- sensor.ecoflow_powerocean_active_fault_codes
- sensor.ecoflow_powerocean_coordinator_status
- sensor.ecoflow_powerocean_grid_import_total (kWh)
- sensor.ecoflow_powerocean_grid_import_today (kWh)
- sensor.ecoflow_powerocean_grid_export_total (kWh)
- sensor.ecoflow_powerocean_grid_export_today (kWh)
- sensor.ecoflow_powerocean_battery_charged_total (kWh)
- sensor.ecoflow_powerocean_battery_charged_today (kWh)
- sensor.ecoflow_powerocean_battery_discharged_total (kWh)
- sensor.ecoflow_powerocean_battery_discharged_today (kWh)
- sensor.ecoflow_powerocean_solar_yield_total (kWh)
- sensor.ecoflow_powerocean_solar_yield_today (kWh)
- sensor.ecoflow_powerocean_house_consumption_today (kWh)
- sensor.ecoflow_powerocean_house_consumption_total (kWh)
- sensor.ecoflow_powerocean_grid_import_today_device (kWh)
- sensor.ecoflow_powerocean_grid_export_today_device (kWh)
- sensor.ecoflow_powerocean_battery_charged_today_device (kWh)
- sensor.ecoflow_powerocean_battery_discharged_today_device (kWh)
- sensor.ecoflow_powerocean_solar_yield_today_device (kWh)
- sensor.ecoflow_powerocean_control_status
- number.ecoflow_powerocean_charge_power (W)
- number.ecoflow_powerocean_discharge_power (W)
- number.ecoflow_powerocean_export_power (W)
- number.ecoflow_powerocean_charge_limit (%)
- number.ecoflow_powerocean_battery_reserve (%)
- number.ecoflow_powerocean_minimum_soc_limit (%)
- number.ecoflow_powerocean_led_brightness (%)
- select.ecoflow_powerocean_battery_mode ["automatic",....]
- switch.ecoflow_powerocean_battery_saver_mode
- switch.ecoflow_powerocean_modbus_control (toggle; renamed from `switch.garage_ecoflow_powerocean_modbus_control`)

### ModBus control: step 1 of any automation that commands the battery

**Turn `switch.ecoflow_powerocean_modbus_control` on before sending any command.** While it is off the inverter runs on EcoFlow's own logic (app modes and schedules) and ignores commands from HA, so changing the entities below has no effect:

- `select.ecoflow_powerocean_battery_mode`
- `number.ecoflow_powerocean_charge_power`, `discharge_power`, `export_power`
- `number.ecoflow_powerocean_charge_limit`, `battery_reserve`, `minimum_soc_limit`
- `switch.ecoflow_powerocean_battery_saver_mode`

Reading sensors works either way. Check `binary_sensor.ecoflow_powerocean_modbus_control` (read-only status) and `sensor.ecoflow_powerocean_control_status` to confirm control is active before relying on a command.

Notes for automation authors:
- Confirmed: with the switch off the commands above do not take effect; with it on they do.
- Not verified: what the inverter does if HA stops while it is in control (the Modbus map has a `heartbeat` register, 40608, which suggests it expects regular contact). Prefer turning control on only while a command is needed, and turning it off again afterwards, rather than leaving it on permanently.
- Some entities on this device (about two dozen, e.g. `sensor.garage_ecoflow_powerocean_grid_side_voltage_l1`, `binary_sensor.garage_ecoflow_powerocean_modbus_control_device`, `switch.garage_ecoflow_powerocean_grid_feed_in`) carry a `garage_` prefix while the rest do not. Check the exact ID in Developer Tools -> States rather than assuming.

### API only

- sensor.ecoflow_powerocean_home_power (W)
- sensor.ecoflow_powerocean_battery_charge_power (W)
- sensor.ecoflow_powerocean_battery_discharge_power (W)
- sensor.ecoflow_powerocean_grid_import_power (W)
- sensor.ecoflow_powerocean_grid_export_power (W)
- sensor.ecoflow_powerocean_battery_soh (%)
- sensor.ecoflow_powerocean_battery_cycles
- sensor.ecoflow_powerocean_battery_remaining_capacity (Wh)
- sensor.ecoflow_powerocean_solar_energy (kWh)
- sensor.ecoflow_powerocean_home_energy (kWh)
- sensor.ecoflow_powerocean_grid_import_energy (kWh)
- sensor.ecoflow_powerocean_grid_export_energy (kWh)
- sensor.ecoflow_powerocean_battery_charge_energy (kWh)
- sensor.ecoflow_powerocean_battery_discharge_energy (kWh)
- sensor.ecoflow_powerocean_grid_phase_a_voltage (V)
- sensor.ecoflow_powerocean_grid_phase_b_voltage (V)
- sensor.ecoflow_powerocean_grid_phase_c_voltage (V)
- sensor.ecoflow_powerocean_grid_phase_a_active_power (W)
- sensor.ecoflow_powerocean_grid_phase_b_active_power (W)
- sensor.ecoflow_powerocean_grid_phase_c_active_power (W)
- sensor.ecoflow_powerocean_grid_phase_a_current (A)
- sensor.ecoflow_powerocean_grid_phase_b_current (A)
- sensor.ecoflow_powerocean_grid_phase_c_current (A)
- sensor.ecoflow_powerocean_feed_mode
- sensor.ecoflow_powerocean_work_mode
- sensor.ecoflow_powerocean_grid_status
- sensor.ecoflow_powerocean_battery_charge_discharge_state
- sensor.ecoflow_powerocean_pack_1_soc (%)
- sensor.ecoflow_powerocean_pack_1_power (W)
- sensor.ecoflow_powerocean_pack_1_soh (%)
- sensor.ecoflow_powerocean_pack_1_cycles
- sensor.ecoflow_powerocean_pack_1_voltage (V)
- sensor.ecoflow_powerocean_pack_1_current (A)
- sensor.ecoflow_powerocean_pack_1_remaining_capacity (Wh)
