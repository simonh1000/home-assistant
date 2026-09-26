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

- ModBus: MaxGrmm/EF-PowerOcean-TcpModbus 
- MQTT/API: https://github.com/shuette42/ecoflow-energy-ha 
- Most popular but lack PowerOcean: https://github.com/tolwi/hassio-ecoflow-cloud

### API values

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

Lots of sensors but no selects (on the cloud API, using ModBus should surface some)