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
(https://github.com/shuette42/ecoflow-energy-ha)

mbpoll -m tcp -a 1 -t 4 -r 0 -c 10 192.168.0.165

Lots of sensors but no selects (on the cloud API, using ModBus should surface some)
