{% set east = states('sensor.energy_production_tomorrow') | float(0) %}
{% set south = states('sensor.energy_production_tomorrow_2') | float(0) %}
{% set produced = east + south %}

{# EcoFlow S1 Vloer nameplate capacity — see background.md. #}
{% set battery_capacity_kwh = 5.1 %}
{% set soc_at_sunrise = 10 %}
{% set background_load_kw = states('input_number.solar_background_load_kw') | float(0.15) %}

{# Tomorrow's day length isn't cleanly derivable from sun.sun (next_rising/
   next_setting roll over independently depending on time of day), so this
   reuses today's daylight length as a close approximation — it only drifts
   by minutes day to day. #}
{% set next_rising = as_timestamp(state_attr('sun.sun', 'next_rising')) %}
{% set next_setting = as_timestamp(state_attr('sun.sun', 'next_setting')) %}
{% set today_sunrise = next_rising if next_rising < next_setting else next_rising - 86400 %}
{% set daylight_hours = (next_setting - today_sunrise) / 3600 %}

{% set background_estimate = daylight_hours * background_load_kw %}
{% set battery_room_kwh = battery_capacity_kwh * (1 - soc_at_sunrise / 100) %}

{% set gross_surplus = [produced - background_estimate, 0] | max %}
{% set surplus = [gross_surplus - battery_room_kwh, 0] | max %}

# Est. Surplus: {{ surplus | round(1) }} kWh

## {{ produced | round(1) }} kWh forecast solar

Background use estimate: {{ daylight_hours | round(1) }}h daylight × {{ background_load_kw }} kW ≈ {{ background_estimate | round(1) }} kWh

Gross surplus (after background use): {{ gross_surplus | round(1) }} kWh

Battery assumed {{ soc_at_sunrise }}% at sunrise ({{ battery_room_kwh | round(1) }} kWh still to fill)
