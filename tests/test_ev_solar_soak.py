"""Tests for the solar-soak controller (src/helpers/solar_soak.yaml + ev-solar-soak*.yaml).

The real helper package and automations are loaded into a headless HA core. Time is
frozen *before* anything is set up (template delay_on/delay_off and the automation's
time_pattern schedule from the clock), then advanced in jumps.
"""
from datetime import timedelta
from pathlib import Path

import pytest
import yaml
import homeassistant.util.dt as dt_util
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_fire_time_changed

ROOT = Path(__file__).parent.parent / "src"
MODE = "select.ohme_home_pro_delta_11kw_charge_mode"
APPROVAL = "switch.ohme_home_pro_delta_11kw_require_approval"


def _load(path):
    with (ROOT / path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _midday_tomorrow():
    return (dt_util.now() + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)


async def _advance(hass, freezer, minutes):
    when = dt_util.now() + timedelta(minutes=minutes)
    freezer.move_to(when)
    async_fire_time_changed(hass, when)
    await hass.async_block_till_done()


def _set_sun(hass, hours_left):
    setting = (dt_util.now() + timedelta(hours=hours_left)).isoformat()
    hass.states.async_set("sun.sun", "above_horizon", {"next_setting": setting})


@pytest.fixture
async def soak(hass, freezer):
    """Helper package + both automations, with a sunny, charged, plugged-in starting state."""
    freezer.move_to(_midday_tomorrow())

    helpers = _load("helpers/solar_soak.yaml")
    await async_setup_component(hass, "input_boolean", {"input_boolean": helpers["input_boolean"]})
    await async_setup_component(hass, "input_number", {"input_number": helpers["input_number"]})
    await async_setup_component(hass, "template", {"template": helpers["template"]})

    # Stand-ins for services that live in other integrations
    def _ids(call):
        ids = call.data["entity_id"]  # a list when it comes from an action's `target:`
        return [ids] if isinstance(ids, str) else ids

    async def set_option(call):
        for eid in _ids(call):
            hass.states.async_set(eid, call.data["option"])

    async def turn_on(call):
        for eid in _ids(call):
            hass.states.async_set(eid, "on")

    async def turn_off(call):
        for eid in _ids(call):
            hass.states.async_set(eid, "off")

    async def noop(call):
        pass

    hass.services.async_register("select", "select_option", set_option)
    hass.services.async_register("switch", "turn_on", turn_on)
    hass.services.async_register("switch", "turn_off", turn_off)
    hass.services.async_register("script", "notify_simon", noop)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "plugged_in")
    hass.states.async_set(MODE, "paused")
    hass.states.async_set(APPROVAL, "on")
    hass.states.async_set("sensor.ecoflow_powerocean_battery_soc", "95")
    hass.states.async_set("sensor.ecoflow_powerocean_solar_power", "1500")
    hass.states.async_set("sensor.ecoflow_powerocean_available_battery_discharge_power", "3300")
    hass.states.async_set("sensor.ecoflow_powerocean_house_power", "200")
    hass.states.async_set("sensor.p1_meter_power", "50")
    _set_sun(hass, 6)

    await async_setup_component(hass, "automation", {"automation": [
        _load("automations/ev-solar-soak.yaml"),
        _load("automations/ev-solar-soak-mode.yaml"),
    ]})
    await hass.async_block_till_done()


async def _soak_on(hass):
    await hass.services.async_call("input_boolean", "turn_on",
                                   {"entity_id": "input_boolean.ev_solar_soak"}, blocking=True)
    await hass.async_block_till_done()


async def test_starts_charging_when_all_conditions_hold(hass, soak, freezer):
    await _soak_on(hass)
    await _advance(hass, freezer, 11)
    assert hass.states.get("binary_sensor.solar_soak_start_ok").state == "on"
    assert hass.states.get(MODE).state == "max_charge"


async def test_does_nothing_when_soak_mode_off(hass, soak, freezer):
    await _advance(hass, freezer, 11)
    assert hass.states.get(MODE).state == "paused"


async def test_waits_for_battery_to_reach_start_level(hass, soak, freezer):
    hass.states.async_set("sensor.ecoflow_powerocean_battery_soc", "85")
    await _soak_on(hass)
    await _advance(hass, freezer, 11)
    assert hass.states.get(MODE).state == "paused"


async def test_does_not_start_with_little_daylight_left(hass, soak, freezer):
    _set_sun(hass, 2)  # needs 3 h
    await _soak_on(hass)
    await _advance(hass, freezer, 11)
    assert hass.states.get(MODE).state == "paused"


async def test_does_not_start_when_solar_cannot_carry_the_car(hass, soak, freezer):
    # 500 W solar + 3300 W battery < 200 W house + 4140 W car
    hass.states.async_set("sensor.ecoflow_powerocean_solar_power", "500")
    await _soak_on(hass)
    await _advance(hass, freezer, 11)
    assert hass.states.get(MODE).state == "paused"


async def _start_charging(hass, freezer):
    await _soak_on(hass)
    await _advance(hass, freezer, 11)
    assert hass.states.get(MODE).state == "max_charge"
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    await hass.async_block_till_done()


async def test_pauses_at_once_when_battery_reaches_floor(hass, soak, freezer):
    await _start_charging(hass, freezer)
    hass.states.async_set("sensor.ecoflow_powerocean_battery_soc", "30")  # floor is 30 (stop at or below)
    # Only 1 minute after starting: no 3 min debounce and no 10 min gap for the floor
    await _advance(hass, freezer, 1)
    assert hass.states.get(MODE).state == "paused"


async def test_does_not_stop_just_above_floor(hass, soak, freezer):
    await _start_charging(hass, freezer)
    hass.states.async_set("sensor.ecoflow_powerocean_battery_soc", "31")
    await _advance(hass, freezer, 14)
    assert hass.states.get(MODE).state == "max_charge"


async def test_pauses_when_grid_is_being_used(hass, soak, freezer):
    await _start_charging(hass, freezer)
    hass.states.async_set("sensor.p1_meter_power", "900")  # limit is 400 W
    await _advance(hass, freezer, 14)  # 3 min debounce + 10 min since the last mode change
    assert hass.states.get(MODE).state == "paused"


async def test_brief_grid_use_does_not_stop_charging(hass, soak, freezer):
    await _start_charging(hass, freezer)
    hass.states.async_set("sensor.p1_meter_power", "900")
    await _advance(hass, freezer, 2)  # shorter than the 3 min debounce
    hass.states.async_set("sensor.p1_meter_power", "50")
    await _advance(hass, freezer, 14)
    assert hass.states.get(MODE).state == "max_charge"


async def test_keeps_charging_while_free(hass, soak, freezer):
    await _start_charging(hass, freezer)
    await _advance(hass, freezer, 30)
    assert hass.states.get(MODE).state == "max_charge"


async def test_mode_switch_controls_ohme_approval(hass, soak):
    await _soak_on(hass)
    assert hass.states.get(APPROVAL).state == "off"
    await hass.services.async_call("input_boolean", "turn_off",
                                   {"entity_id": "input_boolean.ev_solar_soak"}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(APPROVAL).state == "on"
