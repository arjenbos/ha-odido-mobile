import asyncio
import logging
from datetime import timedelta

import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from . import AsyncConfigEntryAuth, PostNLGraphql, OdidoAPI
from .const import DOMAIN
from .jouw_api import PostNLJouwAPI
from .structs.package import Package

_LOGGER = logging.getLogger(__name__)


class OdidoCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize PostNL coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Odido",
            update_interval=timedelta(seconds=90),
        )
        _LOGGER.debug("OdidoCoordinator initialized with update interval: %s", self.update_interval)

    async def _async_update_data(self):
        _LOGGER.debug("Starting data update for Odido.")
        try:
            odido_api: OdidoAPI = self.hass.data[DOMAIN][self.config_entry.entry_id]['odido_api']

            _LOGGER.debug("Get latest subscription data.")

            return await self.hass.async_add_executor_job(odido_api.subscriptions)
        except requests.exceptions.RequestException as exception:
            _LOGGER.error("Network error during PostNL data update: %s", exception, exc_info=True)
            raise UpdateFailed("Unable to update PostNL data") from exception
