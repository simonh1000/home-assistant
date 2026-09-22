import logging
import pytest
import yaml
from pathlib import Path
from homeassistant.setup import async_setup_component
from homeassistant.const import EVENT_CALL_SERVICE

# Suppress verbose Home Assistant core debug logs
logging.getLogger("homeassistant").setLevel(logging.WARNING)
logging.getLogger("pytest_homeassistant_custom_component").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

pytest_plugins = ["pytest_homeassistant_custom_component"]

GUARDIAN_YAML_PATH = Path(__file__).parent.parent / "src" / "automations" / "ev-capacity-guardian.yaml"

@pytest.fixture
def guardian_automation_config():
    with GUARDIAN_YAML_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture
async def setup_ha_guardian(hass, guardian_automation_config):
    """Set up Home Assistant components required by EV Capacity Guardian."""
    # Setup input_select
    await async_setup_component(hass, "input_select", {
        "input_select": {
            "ev_guardian_state": {
                "name": "EV Guardian State",
                "options": ["idle", "yielding", "cooldown"],
                "initial": "idle"
            }
        }
    })

    # Setup input_boolean
    await async_setup_component(hass, "input_boolean", {
        "input_boolean": {
            "ev_cooking_over": {
                "name": "EV Cooking Over",
                "initial": "off"
            }
        }
    })

    # Track all service calls made by Home Assistant
    service_calls = []

    async def service_listener(event):
        data = event.data
        domain = data.get("domain")
        service = data.get("service")
        service_data = data.get("service_data", {})
        target_dict = data.get("target", {})
        
        service_calls.append(data)

        # Extract target entity IDs
        target_entities = target_dict.get("entity_id") or service_data.get("entity_id") or []
        if isinstance(target_entities, str):
            target_entities = [target_entities]

        # Handle select.select_option targeting input_select entity or select entity
        if domain == "select" and service == "select_option":
            option = service_data.get("option")
            for target in target_entities:
                if target == "input_select.ev_guardian_state" and option:
                    await hass.services.async_call(
                        "input_select", 
                        "select_option", 
                        {"entity_id": "input_select.ev_guardian_state", "option": option},
                        blocking=True
                    )
                elif target == "select.ohme_home_pro_delta_11kw_charge_mode" and option:
                    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", option)

    hass.bus.async_listen(EVENT_CALL_SERVICE, service_listener)

    # Dummy service handlers for external services so call_service doesn't raise MissingService
    async def dummy_handler(call):
        pass

    hass.services.async_register("script", "notify_both_phones", dummy_handler)
    hass.services.async_register("script", "notify_simon", dummy_handler)
    hass.services.async_register("select", "select_option", dummy_handler)

    # Initial states for sensors
    hass.states.async_set("sensor.ohme_home_pro_delta_11kw_status", "charging")
    hass.states.async_set("sensor.p1_meter_power", "300")
    hass.states.async_set("select.ohme_home_pro_delta_11kw_charge_mode", "smart_charge")

    # Load real automation file into Home Assistant core
    await async_setup_component(hass, "automation", {
        "automation": [guardian_automation_config]
    })

    await hass.async_block_till_done()

    return service_calls
