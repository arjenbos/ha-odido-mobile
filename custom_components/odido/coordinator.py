"""Data update coordinator for the Odido integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from math import floor
from typing import Any, Dict

import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OdidoAPI
from .const import DOMAIN
from .structs.Subscription import Subscription

_LOGGER = logging.getLogger(__name__)


class OdidoCoordinator(DataUpdateCoordinator[Dict[str, Dict[str, Any]]]):
    """Class to manage fetching Odido data from the API."""

    def __init__(self, hass: HomeAssistant, api: OdidoAPI) -> None:
        """Initialize the coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=90),
        )

    async def _async_update_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch data from Odido API."""
        try:
            subscriptions: list[Subscription] = await self.hass.async_add_executor_job(
                self.api.subscriptions
            )
        except requests.exceptions.RequestException as err:  # pragma: no cover - network errors
            raise UpdateFailed("Unable to update Odido data") from err

        data: Dict[str, Dict[str, Any]] = {}

        for subscription in subscriptions:
            roaming_bundles = await self.hass.async_add_executor_job(
                self.api.subscription, subscription, "roamingbundles"
            )

            mb_left_in_bundles = 0
            mb_used_in_bundles = 0

            for bundle in roaming_bundles.get("Bundles", []):
                if "NL" in bundle.get("Zones", []):
                    remaining = bundle.get("Remaining", {})
                    used = bundle.get("Used", {})

                    mb_left_in_bundles += floor(remaining.get("Value", 0) / 1024)
                    mb_used_in_bundles += floor(used.get("Value", 0) / 1024)

            data[subscription.msisdn] = {
                "subscription": subscription,
                "mb_left_in_bundles": mb_left_in_bundles,
                "mb_used_in_bundles": mb_used_in_bundles,
            }

        return data

