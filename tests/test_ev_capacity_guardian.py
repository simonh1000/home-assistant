import pytest
from datetime import timedelta
import homeassistant.util.dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

async def test_high_load_pauses_ev(hass, setup_ha_guardian, freezer):
    """Test sustained high load (>6kW for 30s) while EV is charging pauses EV."""
    service_calls = setup_ha_guardian

    # EV charging, low house power initially
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    hass.states.async_set("sensor.p1_meter_power", "300")
    await hass.async_block_till_done()

    # Trigger high house load
    hass.states.async_set("sensor.p1_meter_power", "6500")
    await hass.async_block_till_done()

    # Advance time by 31s
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    # Check state updates
    assert hass.states.get("input_select.ev_guardian_state").state == "yielding"

    # Check service call actions recorded
    pause_calls = [
        c for c in service_calls 
        if c.get("domain") == "select" and c.get("service") == "select_option" and (c.get("service_data") or {}).get("option") == "paused"
    ]
    assert len(pause_calls) == 1


async def test_high_load_when_not_charging(hass, setup_ha_guardian, freezer):
    """Test high load when EV is not charging triggers notification without changing guardian_state to yielding."""
    service_calls = setup_ha_guardian

    # EV not charging
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "unplugged")
    hass.states.async_set("sensor.p1_meter_power", "300")
    await hass.async_block_till_done()

    # High load > 6kW
    hass.states.async_set("sensor.p1_meter_power", "6500")
    await hass.async_block_till_done()

    # Advance time by 31s
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    # Guardian state should remain idle
    assert hass.states.get("input_select.ev_guardian_state").state == "idle"

    # Notification script should have been called
    notify_calls = [
        c for c in service_calls 
        if c.get("domain") == "script" and c.get("service") == "notify_both_phones"
    ]
    assert len(notify_calls) == 1
    assert "Not the EV" in notify_calls[0].get("service_data", {}).get("title", "")


async def test_quiet_house_yielding_to_cooldown(hass, setup_ha_guardian, freezer):
    """Test house load <500W for 2 mins while yielding transitions to cooldown."""
    service_calls = setup_ha_guardian

    # Set state to yielding
    await hass.services.async_call("input_select", "select_option", {
        "entity_id": "input_select.ev_guardian_state",
        "option": "yielding"
    }, blocking=True)
    
    hass.states.async_set("sensor.p1_meter_power", "1000")
    await hass.async_block_till_done()

    # Power drops below 500W
    hass.states.async_set("sensor.p1_meter_power", "300")
    await hass.async_block_till_done()

    # Advance time by 2 mins 1 second
    freezer.tick(timedelta(minutes=2, seconds=1))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    assert hass.states.get("input_select.ev_guardian_state").state == "cooldown"
