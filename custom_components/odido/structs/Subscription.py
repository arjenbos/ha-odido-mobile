import logging
from dataclasses import dataclass
from typing import Optional

from .Agreement import Agreement

@dataclass
class Subscription:
    link_id: str
    customer_number: int
    is_favorite: bool
    msisdn: str
    status: str
    alias: str
    role: str
    subscription_url: str
    contract_type: str
    customer_type: str
    subscription_type: str
    is_admin: bool
    agreement: Agreement
    visitor_key_for_externals: str
    fixed_subscription_url: Optional[str]
    order: Optional[str]
    disconnection_date_time: Optional[str]
    is_small_business: bool
    is_child_activated: bool
    external_subscription_id: Optional[str]
    is_child_token: bool
    order_status: Optional[str]
    is_end_user_available: bool
    is_eligible_for_child_token: bool

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            link_id=data['LinkId'],
            customer_number=data['CustomerNumber'],
            is_favorite=data['IsFavorite'],
            msisdn=data['MSISDN'],
            status=data['Status'],
            alias=data['Alias'],
            role=data['Role'],
            subscription_url=data['SubscriptionURL'],
            contract_type=data['ContractType'],
            customer_type=data['CustomerType'],
            subscription_type=data['SubscriptionType'],
            is_admin=data['IsAdmin'],
            agreement=Agreement.from_dict(data['Agreement']),
            visitor_key_for_externals=data['VisitorKeyForExternals'],
            fixed_subscription_url=data['FixedSubscriptionURL'],
            order=data['Order'],
            disconnection_date_time=data['DisconnectionDateTime'],
            is_small_business=data['IsSmallBusiness'],
            is_child_activated=data['IsChildActivated'],
            external_subscription_id=data['ExternalSubscriptionId'],
            is_child_token=data['IsChildToken'],
            order_status=data['OrderStatus'],
            is_end_user_available=data['isEndUserAvailable'],
            is_eligible_for_child_token=data['isEligibleForChildToken'],
        )