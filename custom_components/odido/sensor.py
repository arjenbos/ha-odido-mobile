from __future__ import annotations

import logging
from math import floor
from typing import Callable

from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from .structs.Subscription import Subscription
from .const import DOMAIN
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up sensor platform.")

    odido_api = hass.data[DOMAIN][entry.entry_id]["odido_api"]

    subscriptions = await hass.async_add_executor_job(odido_api.subscriptions)

    _LOGGER.debug(subscriptions)

    sensors = []

    for subscription in subscriptions:
        roaming_bundles = await hass.async_add_executor_job(odido_api.subscription, subscription, 'roamingbundles')
        mb_left_in_bundles = 0
        mb_used_in_bundles = 0
        _LOGGER.debug(roaming_bundles)
        for bundle in roaming_bundles.get('Bundles', []):
            if "NL" in bundle.get('Zones', []):
                remaining = bundle.get("Remaining", {})
                used = bundle.get("Used", {})

                _LOGGER.debug("NL zone found in bundle, %s", bundle)
                mb_left_in_bundles += floor(remaining.get("Value", 0) / 1024)
                mb_used_in_bundles += floor(used.get("Value", 0) / 1024)

        _LOGGER.debug("Data left in roaming bundles: %s MB", mb_left_in_bundles)
        _LOGGER.debug("Data used in roaming bundles: %s MB", mb_used_in_bundles)

        sensors.append(
            OdidoSubscriptionSensor(
                OdidoEntityDescription(
                    key="msisdn",
                    name="Phone Number",
                    value_fn=lambda sensor: sensor._subscription.msisdn,
                ),
                subscription=subscription,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                OdidoEntityDescription(
                    key="agreement.start_date",
                    name="Start Date",
                    device_class=SensorDeviceClass.DATE,
                    value_fn=lambda sensor: sensor._subscription.agreement.start_date.strftime("%Y-%m-%d"),
                ),
                subscription=subscription,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                OdidoEntityDescription(
                    key="data_used",
                    name="Data used",
                    device_class=SensorDeviceClass.DATA_SIZE,
                    value_fn=lambda sensor: sensor.mb_used_in_bundles,
                ),
                subscription=subscription,
                mb_used_in_bundles=mb_used_in_bundles,
            )
        )

        sensors.append(
            OdidoSubscriptionSensor(
                OdidoEntityDescription(
                    key="data_left",
                    name="Data Left",
                    device_class=SensorDeviceClass.DATA_SIZE,
                    value_fn=lambda sensor: sensor.mb_left_in_bundles,
                ),
                subscription=subscription,
                mb_left_in_bundles=mb_left_in_bundles,
            )
        )

    async_add_entities(sensors)


def get_nested_attr(obj, attr_path, default=None):
    try:
        for attr in attr_path.split('.'):
            obj = getattr(obj, attr)
        return obj
    except AttributeError:
        return default

class OdidoSubscriptionSensor(Entity):
    """Representation of an Odido subscription sensor."""

    entity_description: OdidoEntityDescription

    def __init__(
        self,
        entity_description: OdidoEntityDescription,
        subscription: Subscription,
        mb_left_in_bundles: float = 0,
        mb_used_in_bundles: float = 0,
    ):
        """Initialize the sensor."""
        self.entity_description = entity_description
        self._subscription = subscription
        self.mb_left_in_bundles = mb_left_in_bundles
        self.mb_used_in_bundles = mb_used_in_bundles

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._subscription.msisdn)
            },
            name=self._subscription.alias or self._subscription.msisdn,
            manufacturer="Odido",

        )

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the sensor."""
        return f"{self._subscription.msisdn}_{self.entity_description.key}"

    @property
    def extra_state_attributes(self):
        """Return the attribution for the sensor."""

        return {
            "subscription_url": self._subscription.subscription_url,
        }

@dataclass(frozen=True, kw_only=True)
class OdidoEntityDescription(SensorEntityDescription):
    """Describes Odido sensor entity."""

    value_fn: Callable[[OdidoSubscriptionSensor], float | str | None] = lambda _: None