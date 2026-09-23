import pytest
from datetime import datetime, timedelta
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


async def test_dinner_lockout_activates_cooking_state(hass, setup_ha_guardian, freezer):
    """Test dinner window at 18:15 sets ev_guardian_state = cooking and pauses charging."""
    service_calls = setup_ha_guardian

    # Set initial time to 18:14:59
    start_time = datetime(2026, 9, 23, 18, 14, 59, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    freezer.move_to(start_time)
    async_fire_time_changed(hass, start_time)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "smart_charge")
    hass.states.async_set("input_select.ev_guardian_state", "idle")
    await hass.async_block_till_done()

    # Advance virtual clock to 18:15:00
    at_dinner = start_time + timedelta(seconds=1)
    freezer.move_to(at_dinner)
    async_fire_time_changed(hass, at_dinner)
    await hass.async_block_till_done()

    # Verify ev_guardian_state is set to 'cooking' and charge mode is 'paused'
    assert hass.states.get("input_select.ev_guardian_state").state == "cooking"
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "paused"


async def test_plugin_during_cooking_pauses_charger(hass, setup_ha_guardian):
    """Test plugging in car while ev_guardian_state == 'cooking' immediately pauses charger."""
    service_calls = setup_ha_guardian

    # Car initially unplugged
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "unplugged")
    await hass.async_block_till_done()

    # Set guardian state to 'cooking'
    await hass.services.async_call("input_select", "select_option", {
        "entity_id": "input_select.ev_guardian_state",
        "option": "cooking"
    }, blocking=True)
    await hass.async_block_till_done()

    # Car status changes to 'charging'
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    await hass.async_block_till_done()

    # Verify charger is paused
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "paused"
