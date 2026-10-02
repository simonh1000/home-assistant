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


def _tomorrow_at(hour, minute, second=0):
    """Local time tomorrow. Automation time triggers are scheduled from the real clock when
    set up, so tests must target a time on or after their next occurrence (never a fixed date)."""
    return (dt_util.now() + timedelta(days=1)).replace(
        hour=hour, minute=minute, second=second, microsecond=0
    )


async def _jump_to(hass, freezer, when):
    freezer.move_to(when)
    async_fire_time_changed(hass, when)
    await hass.async_block_till_done()


async def _skip_past_dinner_start(hass, freezer):
    """Fire the 18:15 trigger (jumping straight to 20:30 would fire it too, late) and settle."""
    await _jump_to(hass, freezer, _tomorrow_at(19, 0))


def _set_mode_calls(service_calls, option):
    return [
        c for c in service_calls
        if c.get("domain") == "select" and c.get("service") == "select_option"
        and (c.get("service_data") or {}).get("option") == option
    ]


async def test_dinner_lockout_activates_cooking_state(hass, setup_ha_guardian, freezer):
    """Test dinner window at 18:15 sets ev_guardian_state = cooking and pauses charging."""
    start = _tomorrow_at(18, 14, 59)
    freezer.move_to(start)
    async_fire_time_changed(hass, start)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "smart_charge")
    hass.states.async_set("input_select.ev_guardian_state", "idle")
    await hass.async_block_till_done()

    await _jump_to(hass, freezer, start + timedelta(seconds=1))

    assert hass.states.get("input_select.ev_guardian_state").state == "cooking"
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "paused"


@pytest.mark.parametrize("prior_state", ["yielding", "cooldown"])
async def test_dinner_start_while_yielding_or_cooldown_enters_cooking(
    hass, setup_ha_guardian, freezer, prior_state
):
    """A load pause that is already running at 18:15 hands over to the dinner window."""
    service_calls = setup_ha_guardian
    start = _tomorrow_at(18, 14, 59)
    freezer.move_to(start)
    async_fire_time_changed(hass, start)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "paused")
    hass.states.async_set("input_select.ev_guardian_state", prior_state)
    await hass.async_block_till_done()

    await _jump_to(hass, freezer, start + timedelta(seconds=1))

    assert hass.states.get("input_select.ev_guardian_state").state == "cooking"
    # Already paused, so no second pause command
    assert _set_mode_calls(service_calls, "paused") == []


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


async def test_dinner_end_returns_to_idle_and_resumes(hass, setup_ha_guardian, freezer):
    """At 20:30 cooking -> idle and a paused charger goes back to smart_charge."""
    await _skip_past_dinner_start(hass, freezer)
    start = _tomorrow_at(20, 29, 59)
    freezer.move_to(start)
    async_fire_time_changed(hass, start)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "cooking")
    await hass.async_block_till_done()

    await _jump_to(hass, freezer, start + timedelta(seconds=1))

    assert hass.states.get("input_select.ev_guardian_state").state == "idle"
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "smart_charge"


async def test_dinner_end_does_not_touch_load_pause(hass, setup_ha_guardian, freezer):
    """20:30 must not resume the EV when guardian is yielding because of house load."""
    service_calls = setup_ha_guardian
    await _skip_past_dinner_start(hass, freezer)
    start = _tomorrow_at(20, 29, 59)
    freezer.move_to(start)
    async_fire_time_changed(hass, start)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "yielding")
    await hass.async_block_till_done()

    await _jump_to(hass, freezer, start + timedelta(seconds=1))

    assert hass.states.get("input_select.ev_guardian_state").state == "yielding"
    assert _set_mode_calls(service_calls, "smart_charge") == []


async def test_high_load_during_cooking_keeps_cooking(hass, setup_ha_guardian, freezer):
    """High load while cooking (EV already paused) must not change state or resume/pause."""
    service_calls = setup_ha_guardian
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "cooking")
    hass.states.async_set("sensor.p1_meter_power", "300")
    await hass.async_block_till_done()

    hass.states.async_set("sensor.p1_meter_power", "6500")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()

    assert hass.states.get("input_select.ev_guardian_state").state == "cooking"
    assert _set_mode_calls(service_calls, "paused") == []


async def test_safety_net_forces_idle_and_resumes(hass, setup_ha_guardian, freezer):
    """At 22:30 any guardian state returns to idle and a paused charger is resumed."""
    start = _tomorrow_at(22, 29, 59)
    freezer.move_to(start)
    async_fire_time_changed(hass, start)

    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "cooldown")
    await hass.async_block_till_done()

    await _jump_to(hass, freezer, start + timedelta(seconds=1))

    assert hass.states.get("input_select.ev_guardian_state").state == "idle"
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "smart_charge"


async def test_done_cooking_button_ends_cooking_and_resumes(hass, setup_ha_guardian):
    """The notification/Done Cooking action ends the dinner window early."""
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "cooking")
    await hass.async_block_till_done()

    hass.bus.async_fire("mobile_app_notification_action", {"action": "EV_COOKING_OVER"})
    await hass.async_block_till_done()

    assert hass.states.get("input_select.ev_guardian_state").state == "idle"
    assert hass.states.get("select.ohme_home_pro_delta_11kw_charge_mode").state == "smart_charge"


async def test_done_cooking_button_ignored_when_not_cooking(hass, setup_ha_guardian):
    """Pressing the button during a load pause must not resume the EV."""
    service_calls = setup_ha_guardian
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "paused")
    hass.states.async_set("input_select.ev_guardian_state", "yielding")
    await hass.async_block_till_done()

    hass.bus.async_fire("mobile_app_notification_action", {"action": "EV_COOKING_OVER"})
    await hass.async_block_till_done()

    assert hass.states.get("input_select.ev_guardian_state").state == "yielding"
    assert _set_mode_calls(service_calls, "smart_charge") == []
