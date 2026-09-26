{% set east = states('sensor.energy_production_today') | float(0) %}
{% set south = states('sensor.energy_production_today_2') | float(0) %}
{% set produced = east + south %}

{# EcoFlow S1 Vloer nameplate capacity — see background.md. Not read from a
   sensor because nothing here reports usable/rated capacity live. #}
{% set battery_capacity_kwh = 5.1 %}
{% set soc_now = states('sensor.ecoflow_powerocean_battery_soc') | float(0) %}
{% set soc_daybreak = states('input_number.battery_soc_at_daybreak') | float(soc_now) %}
{% set background_load_kw = states('input_number.solar_background_load_kw') | float(0.15) %}

{# Daylight length for today. sun.sun only ever exposes the *next* rising/
   setting, so during the day next_rising has already rolled over to
   tomorrow — back it off by 24h to recover today's sunrise. This drifts by
   the day-length delta (seconds, not minutes) so it's fine here. #}
{% set next_rising = as_timestamp(state_attr('sun.sun', 'next_rising')) %}
{% set next_setting = as_timestamp(state_attr('sun.sun', 'next_setting')) %}
{% set today_sunrise = next_rising if next_rising < next_setting else next_rising - 86400 %}
{% set daylight_hours = (next_setting - today_sunrise) / 3600 %}

{# The simple estimate: nothing here can isolate "background-only" import
   during solar hours (P1 import reflects grid draw only, since panels feed
   the house directly too), so background use during solar hours is modelled
   as a flat rate × daylight hours rather than measured. #}
{% set background_estimate = daylight_hours * background_load_kw %}

{# Room the battery still has to fill today, as of daybreak. Whatever the
   battery still needs isn't "surplus" — it'll be soaked up by self-consumption
   before anything reaches an appliance or the car. #}
{% set battery_room_kwh = battery_capacity_kwh * (1 - soc_daybreak / 100) %}

{% set surplus = [produced - background_estimate - battery_room_kwh, 0] | max %}

# Est Surplus: {{ surplus | round(1) }} kWh

## {{ produced | round(1) }} kWh produced today

Battery: {{ soc_now | round(0) }}% now, {{ soc_daybreak | round(0) }}% at daybreak ({{ battery_room_kwh | round(1) }} kWh still to fill)

Background use estimate: {{ daylight_hours | round(1) }}h daylight × {{ background_load_kw }} kW ≈ {{ background_estimate | round(1) }} kWh


Assumptions: background load during solar hours is a flat rate (`input_number.solar_background_load_kw`, default 0.15 kW — background.md puts normal background use at 0.1–0.25 kW), not metered directly. Battery capacity is the 5.1 kWh nameplate figure, not a live reading. SoC at daybreak is captured by the `solar_daybreak_snapshot` automation at sunrise.
