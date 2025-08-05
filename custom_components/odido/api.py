import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from typing import List

from .structs.Subscription import Subscription

_LOGGER = logging.getLogger(__name__)

class OdidoAPI:
    """Class to handle Odido API interactions."""

    base_url = "https://capi.odido.nl"

    buying_code = "A0DAY01"

    def __init__(self, access_token: str):
        """Initialize the OdidoAPI."""

        self.client = requests.Session()
        self.client.mount(
            prefix='https://',
            adapter=HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    backoff_factor=3
                )
            )
        )

        self.client.headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + access_token
        }

    @staticmethod
    def generate_access_token(refresh_token: str):
        """Generate a new access token using the refresh token."""
        _LOGGER.debug("Generating new access token using refresh token")

        response = requests.post(
            "https://capi.odido.nl/createtoken",
            headers={
                "accept": "application/json,application/vnd.capi.tmobile.nl.createtoken.v1+json",
                "authorization": "Basic OWhhdnZhdDZobTBiOTYyaTo=",
                "grant_type": "authorization_code",
            },
            json={
                "AuthorizationCode": refresh_token
            }
        )

        _LOGGER.debug(response.status_code)
        _LOGGER.debug("Response from token generation: %s", response.headers)
        _LOGGER.debug(response.text)

        if "ErrorCode" in response.headers:
            _LOGGER.error("Error generating access token: %s", response.headers["ErrorText"])
            return {"ErrorCode": response.headers.get("ErrorText", "Unknown error")}

        return {
            "access_token": response.headers.get('Accesstoken')
        }

    def me(self):
        """Fetch user data."""
        _LOGGER.debug("Fetching user data from Odido API")

        response = self.client.get(self.base_url + "/account/current")
        _LOGGER.debug(response)

        return response.json()

    def subscriptions(self):
        """Fetch user subscriptions."""
        _LOGGER.debug("Fetching user subscriptions from Odido API")

        response = self.client.get(self.base_url + "/account/current?resourcelabel=LinkedSubscriptions")

        if response.status_code != 200:
            _LOGGER.error("Failed to fetch subscriptions: %s", response.text)
            return {"ErrorCode": "Failed to fetch subscriptions"}

        response_json = response.json()

        if "Resources" not in response_json:
            _LOGGER.error("No LinkedSubscriptions found in response: %s", response_json)
            return {"ErrorCode": "No subscriptions found"}

        subscriptions_response = self.client.get(response_json["Resources"][0]["Url"])

        subscriptions_json = subscriptions_response.json()

        _LOGGER.debug("Subscription: %s", subscriptions_json)

        subscriptions: List[Subscription] = [
            Subscription.from_dict(item) for item in subscriptions_json['subscriptions']
        ]

        return subscriptions

    def subscription(self, subscription: Subscription, type: str):
        """Fetch a specific subscription by its ID."""
        _LOGGER.debug("Fetching subscription with ID: %s", subscription.link_id)

        response = self.client.get(f"{subscription.subscription_url}/{type}")

        if response.status_code != 200:
            _LOGGER.error("Failed to fetch subscription: %s", response.text)
            return {"ErrorCode": "Failed to fetch subscription"}

        return response.json()

    def buy_bundle(self, subscription_url: str):
        """Buy a bundle for the given subscription."""
        _LOGGER.debug("Buying bundle for subscription %s", subscription_url)

        response = self.client.post(
            f"{subscription_url}/roamingbundles",
            json={
                "Bundles": [{ "BuyingCode": self.buying_code }]
            }
        )

        if response.status_code != 202 and response.reason == "The provided buying code isn't available for purchase.":
            _LOGGER.error("Failed to buy bundle: %s", response.text)
            return {"ErrorCode": "Failed to buy bundle"}

        _LOGGER.debug("Response from buying bundle: %s", response.text)

        return response.json()