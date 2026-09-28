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

### ModBus

- Wire addresses are the protocol doc's hex offset + 40001 (e.g. SOC is 0x020E = 526 in the doc, but 40527 on the wire) — confirmed against MaxGrmm/EF-PowerOcean-TcpModbus's const.py, whose registers (grid_power=40521, battery_power=40525, battery_soc=40527, heartbeat=40608, control_command=40534, ...) all match offset+40001 exactly.

update.ecoflow_energy_update: off 

binary_sensor.ecoflow_powerocean_modbus_control: off 

binary_sensor.ecoflow_powerocean_self_powered_mode: on 

binary_sensor.ecoflow_powerocean_intelligent_mode: off 

binary_sensor.ecoflow_powerocean_system_fault: off 

binary_sensor.ecoflow_powerocean_system_powered_on: on 

sensor.ecoflow_powerocean_system_modes: 4116 

sensor.ecoflow_powerocean_house_power: 418 W

sensor.ecoflow_powerocean_grid_power: -2 W

sensor.ecoflow_powerocean_solar_power: 0 W

sensor.ecoflow_powerocean_battery_power: -421 W

sensor.ecoflow_powerocean_battery_soc: 5 %

sensor.ecoflow_powerocean_available_battery_charge_power: 2500 W

sensor.ecoflow_powerocean_available_battery_discharge_power: 3300 W

sensor.ecoflow_powerocean_maximum_inverter_power_dc_to_ac: 6000 W

sensor.ecoflow_powerocean_maximum_rectifier_power_ac_to_dc: 6000 W

sensor.ecoflow_powerocean_battery_nominal_capacity: 5000 Wh

sensor.ecoflow_powerocean_battery_voltage: 50.8 V

sensor.ecoflow_powerocean_battery_current: -8.24 A

sensor.ecoflow_powerocean_battery_temperature: 34.0 °C

sensor.ecoflow_powerocean_grid_voltage_l1: 236.7 V

sensor.ecoflow_powerocean_grid_voltage_l2: 238.2 V

sensor.ecoflow_powerocean_grid_voltage_l3: 237.3 V

sensor.ecoflow_powerocean_grid_current_l1: 1.01 A

sensor.ecoflow_powerocean_grid_current_l2: 1.03 A

sensor.ecoflow_powerocean_grid_current_l3: 1.03 A

sensor.ecoflow_powerocean_inverter_temperature: 30.0 °C

sensor.ecoflow_powerocean_grid_frequency: 50.0 Hz

sensor.ecoflow_powerocean_pv_string_1_voltage: 68.2 V

sensor.ecoflow_powerocean_pv_string_2_voltage: 200.0 V

sensor.ecoflow_powerocean_pv_string_3_voltage: 0.0 V

sensor.ecoflow_powerocean_pv_string_1_current: 0.04 A

sensor.ecoflow_powerocean_pv_string_2_current: 0.08 A

sensor.ecoflow_powerocean_pv_string_3_current: 0.0 A

sensor.ecoflow_powerocean_maximum_feed_in_power: 6000 W

sensor.ecoflow_powerocean_inverter_rated_power: 6000 W

sensor.ecoflow_powerocean_battery_module_count: 1 

sensor.ecoflow_powerocean_battery_1_soc: 5 %

sensor.ecoflow_powerocean_battery_remaining_energy: 0.25 kWh

sensor.ecoflow_powerocean_pv_string_1_power: 0 W

sensor.ecoflow_powerocean_pv_string_2_power: 16 W

sensor.ecoflow_powerocean_pv_string_3_power: 0 W

sensor.ecoflow_powerocean_battery_energy_loss: -0.6 kWh

sensor.ecoflow_powerocean_grid_mode: grid 

sensor.ecoflow_powerocean_operating_mode: self_consumption 

sensor.ecoflow_powerocean_system_power_setpoint: 0 W

sensor.ecoflow_powerocean_inverter_power_setpoint: 0 W

sensor.ecoflow_powerocean_battery_power_setpoint: 0 W

sensor.ecoflow_powerocean_active_fault_count: 0 

sensor.ecoflow_powerocean_active_fault_codes: none 

sensor.ecoflow_powerocean_coordinator_status: success 

sensor.ecoflow_powerocean_grid_import_total: 69.38 kWh

sensor.ecoflow_powerocean_grid_import_today: 2.24 kWh

sensor.ecoflow_powerocean_grid_export_total: 0.51 kWh

sensor.ecoflow_powerocean_grid_export_today: 0.07 kWh

sensor.ecoflow_powerocean_battery_charged_total: 16.45 kWh

sensor.ecoflow_powerocean_battery_charged_today: 1.68 kWh

sensor.ecoflow_powerocean_battery_discharged_total: 17.05 kWh

sensor.ecoflow_powerocean_battery_discharged_today: 0.99 kWh

sensor.ecoflow_powerocean_solar_yield_total: 35.73 kWh

sensor.ecoflow_powerocean_solar_yield_today: 4.17 kWh

sensor.ecoflow_powerocean_house_consumption_today: 5.65 kWh

sensor.ecoflow_powerocean_house_consumption_total: 105.2 kWh

sensor.ecoflow_powerocean_grid_import_today_device: 2.24 kWh

sensor.ecoflow_powerocean_grid_export_today_device: 0.07 kWh

sensor.ecoflow_powerocean_battery_charged_today_device: 1.68 kWh

sensor.ecoflow_powerocean_battery_discharged_today_device: 0.98 kWh

sensor.ecoflow_powerocean_solar_yield_today_device: 4.17 kWh

sensor.ecoflow_powerocean_control_status: no_modbus_control 

number.ecoflow_powerocean_charge_power: unavailable W

number.ecoflow_powerocean_discharge_power: unavailable W

number.ecoflow_powerocean_export_power: unavailable W

number.ecoflow_powerocean_charge_limit: unavailable %

number.ecoflow_powerocean_battery_reserve: unavailable %

number.ecoflow_powerocean_minimum_soc_limit: 0.0 %

number.ecoflow_powerocean_led_brightness: 100.0 %

select.ecoflow_powerocean_battery_mode: unavailable 

switch.ecoflow_powerocean_battery_saver_mode: off

### API values (sensors only!)

sensor.ecoflow_powerocean_solar_power: 830 W

sensor.ecoflow_powerocean_home_power: 4290 W

sensor.ecoflow_powerocean_grid_power: 3460 W

sensor.ecoflow_powerocean_battery_power: 0 W

sensor.ecoflow_powerocean_battery_charge_power: 0 W

sensor.ecoflow_powerocean_battery_discharge_power: 0 W

sensor.ecoflow_powerocean_grid_import_power: 3460 W

sensor.ecoflow_powerocean_grid_export_power: 0 W

sensor.ecoflow_powerocean_battery_soc: 96 %

sensor.ecoflow_powerocean_battery_soh: 100 %

sensor.ecoflow_powerocean_battery_cycles: 2 

sensor.ecoflow_powerocean_battery_remaining_capacity: 4915 Wh

sensor.ecoflow_powerocean_solar_energy: 21.95 kWh

sensor.ecoflow_powerocean_home_energy: 71.83 kWh

sensor.ecoflow_powerocean_grid_import_energy: 51.94 kWh

sensor.ecoflow_powerocean_grid_export_energy: 0.22 kWh

sensor.ecoflow_powerocean_battery_charge_energy: 11.12 kWh

sensor.ecoflow_powerocean_battery_discharge_energy: 7.5 kWh

sensor.ecoflow_powerocean_battery_voltage: 53.5 V

sensor.ecoflow_powerocean_battery_current: -0.0 A

sensor.ecoflow_powerocean_grid_frequency: unknown Hz

sensor.ecoflow_powerocean_pv_string_1_power: 3 W

sensor.ecoflow_powerocean_pv_string_1_voltage: 75.0 V

sensor.ecoflow_powerocean_pv_string_1_current: 0.03 A

sensor.ecoflow_powerocean_pv_string_2_power: 650 W

sensor.ecoflow_powerocean_pv_string_2_voltage: 202.0 V

sensor.ecoflow_powerocean_pv_string_2_current: 3.22 A

sensor.ecoflow_powerocean_grid_phase_a_voltage: 236.7 V

sensor.ecoflow_powerocean_grid_phase_b_voltage: 237.5 V

sensor.ecoflow_powerocean_grid_phase_c_voltage: 236.7 V

sensor.ecoflow_powerocean_grid_phase_a_active_power: -153 W

sensor.ecoflow_powerocean_grid_phase_b_active_power: -163 W

sensor.ecoflow_powerocean_grid_phase_c_active_power: -158 W

sensor.ecoflow_powerocean_grid_phase_a_current: 0.96 A

sensor.ecoflow_powerocean_grid_phase_b_current: 0.99 A

sensor.ecoflow_powerocean_grid_phase_c_current: 1.0 A

sensor.ecoflow_powerocean_feed_mode: no_limit 

sensor.ecoflow_powerocean_work_mode: self_use 

sensor.ecoflow_powerocean_grid_status: not_detected 

sensor.ecoflow_powerocean_battery_charge_discharge_state: unknown 

sensor.ecoflow_powerocean_pack_1_soc: 96 %

sensor.ecoflow_powerocean_pack_1_power: 0 W

sensor.ecoflow_powerocean_pack_1_soh: 100 %

sensor.ecoflow_powerocean_pack_1_cycles: 2 

sensor.ecoflow_powerocean_pack_1_voltage: 53.5 V

sensor.ecoflow_powerocean_pack_1_current: -0.0 A

sensor.ecoflow_powerocean_pack_1_remaining_capacity: 4915 Wh
