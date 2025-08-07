import logging
import requests
import urllib3

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (ConfigEntryNotReady, ConfigEntryAuthFailed, HomeAssistantError)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry, async_entries_for_device

from .api import OdidoAPI
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> True:
    """Set up Odido from config entry."""
    _LOGGER.debug("Setting up Odido")

    _LOGGER.debug("Config entry data: %s", entry.data)

    odido_api = OdidoAPI(
        access_token=entry.data['access_token']
    )

    try:
        userinfo = await hass.async_add_executor_job(odido_api.me)
    except (requests.exceptions.RequestException, urllib3.exceptions.MaxRetryError) as exception:
        raise ConfigEntryNotReady("Unable to retrieve user information from Odido.") from exception

    if "ErrorCode" in userinfo:
        raise ConfigEntryAuthFailed("Unable to retrieve user information from Odido.")

    _LOGGER.debug("User info: %s", userinfo)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "odido_api": odido_api,
    }

    async def handle_buy_bundle(call):
        device_id = call.data["device_id"]
        buying_code = call.data.get("buying_code")

        entity_registry = async_get_entity_registry(hass)
        entries = async_entries_for_device(entity_registry, device_id)

        for entry in entries:
            if (
                entry.domain == "sensor"
                and entry.platform == DOMAIN
                and entry.original_name == "Phone Number"
            ):
                _LOGGER.debug(entry)
                odido_api = hass.data[DOMAIN][entry.config_entry_id]["odido_api"]

                state = hass.states.get(entry.entity_id)

                response = await hass.async_add_executor_job(
                    odido_api.buy_bundle,
                    state.attributes.get("subscription_url"),
                    buying_code,
                )
                _LOGGER.debug(response)

                if "ErrorCode" in response:
                    raise BuyingRoamingBundleError(response.get("ErrorCode"))

                return True

        _LOGGER.error("No valid odido sensor found for device_id %s", device_id)

    hass.services.async_register("odido", "buy_bundle", handle_buy_bundle)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Alpha Innotec config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class BuyingRoamingBundleError(HomeAssistantError):
    """Error raised when an error occurred while buying a roaming bundle."""