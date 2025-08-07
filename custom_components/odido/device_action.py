# custom_components/odido/device_action.py

from homeassistant.const import ATTR_DEVICE_ID, ATTR_ENTITY_ID
from homeassistant.helpers.entity_registry import async_entries_for_device
import voluptuous as vol

from .const import DOMAIN, DEFAULT_BUYING_CODE

ACTION_TYPE_BUY_BUNDLE = "buy_bundle"

async def async_get_actions(hass, device_id):
    """List actions for a device."""
    registry = await hass.helpers.entity_registry.async_get_registry()
    entries = async_entries_for_device(registry, device_id)

    actions = []
    for entry in entries:
        if entry.domain != DOMAIN:
            continue

        actions.append({
            "domain": DOMAIN,
            "type": ACTION_TYPE_BUY_BUNDLE,
            "device_id": device_id,
            "entity_id": entry.entity_id,
        })

    return actions

async def async_call_action_from_config(hass, config, variables, context=None):
    """Execute the action."""
    entity_id = config.get(ATTR_ENTITY_ID)
    device_id = config[ATTR_DEVICE_ID]

    data = {ATTR_DEVICE_ID: device_id}
    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id
    if "buying_code" in config:
        data["buying_code"] = config["buying_code"]

    await hass.services.async_call(
        DOMAIN,
        ACTION_TYPE_BUY_BUNDLE,
        data,
        context=context,
    )


async def async_get_action_capabilities(hass, config):
    """List capabilities of the action."""
    return {
        "extra_fields": vol.Schema(
            {
                vol.Optional("buying_code", default=DEFAULT_BUYING_CODE): vol.Coerce(str)
            }
        )
    }

def async_validate_action_config(hass, config):
    """Validate config if needed (basic passthrough here)."""
    return config

