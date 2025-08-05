from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from cryptography.fernet import Fernet
from urllib.parse import urlparse, parse_qs

from . import OdidoAPI
from .const import DOMAIN, ENCRYPTION_KEY, OAUTH_KEY

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    f = Fernet(ENCRYPTION_KEY)

    _LOGGER.debug("Data received for validation: %s", data)

    parsed_url = urlparse(data.get("refreshTokenUrl", ""))
    query_params = parse_qs(parsed_url.query)

    token = query_params.get("token", [None])[0]

    decrypted_token = f.decrypt(token.encode())
    _LOGGER.debug("Decrypted token: %s", decrypted_token)

    decoded_decrypted = json.loads(decrypted_token.decode())

    decoded_decrypted_access_token = f.decrypt(decoded_decrypted['AccessToken']).decode()

    access_token = await hass.async_add_executor_job(OdidoAPI.generate_access_token, decoded_decrypted_access_token)

    if "ErrorCode" in access_token:
        _LOGGER.error("Error generating access token: %s", access_token)
        raise AuthenticationFailed(access_token["ErrorCode"])

    _LOGGER.debug("Access Token: %s", access_token)

    return {
        "title": "Odido - " + decoded_decrypted.get("sub"),
        "access_token": access_token["access_token"]
    }

    odido_api = OdidoAPI(
        access_token=access_token["access_token"]
    )



    try:
        userinfo = await hass.async_add_executor_job(odido_api.me)
    except Exception as exception:
        _LOGGER.error("Error connecting to Odido API: %s", exception)
        raise CannotConnect from exception

    if "ErrorCode" in userinfo:
        _LOGGER.error("Authentication failed with Odido: %s", userinfo)
        raise AuthenticationFailed("Invalid authorization token.")

    return {"title": "Odido"}


class OdidoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Odido config flow."""

    def __init__(self):
        self.reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data={
                    "access_token": info["access_token"],
                })

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except AuthenticationFailed:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during user setup")
                errors["base"] = "unknown"

        f = Fernet(ENCRYPTION_KEY)

        encrypted_token = f.encrypt(OAUTH_KEY)

        # Convert to URL-safe string
        encrypted_token_str = encrypted_token.decode()

        # Construct the login URL
        login_url = f"https://www.odido.nl/login?returnSystem=app&nav=off&token={encrypted_token_str}"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("refreshTokenUrl", description="Refresh Token URL"): str
            }),
            errors=errors,
            description_placeholders={
                "login_url": login_url
            }
        )

    async def async_step_reauth(self, user_input=None):
        """Handle re-authentication with a new token."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                self.hass.config_entries.async_update_entry(
                    self.reauth_entry,
                    data={
                        **self.reauth_entry.data,
                        "authorizationToken": user_input["authorizationToken"]
                    }
                )

                await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)

                return self.async_abort(reason="reauth_successful")

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except AuthenticationFailed:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth",
            data_schema=vol.Schema({
                vol.Required("authorizationToken", description="Authorization token"): str
            }),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AuthenticationFailed(exceptions.HomeAssistantError):
    """Error to indicate invalid authentication."""
