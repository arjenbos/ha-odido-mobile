from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Agreement:
    rateplan_name: str
    product_name: str
    end_date: datetime
    start_date: datetime
    status: str
    rateplan_type: str
    renewal_eligibility_date: datetime
    is_possible_renewal_candidate: bool
    is_already_renewed: bool
    product_code: str
    sort_order: str
    show_on_dashboard: bool
    rateplan_code: str

    @staticmethod
    def parse_date(date_str: str) -> datetime:
        ms = int(date_str.strip('/Date()\\/'))
        return datetime.utcfromtimestamp(ms / 1000)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            rateplan_name=data['RateplanName'],
            product_name=data['ProductName'],
            end_date=cls.parse_date(data['EndDate']),
            start_date=cls.parse_date(data['StartDate']),
            status=data['Status'],
            rateplan_type=data['RateplanType'],
            renewal_eligibility_date=cls.parse_date(data['RenewalEligibilityDate']),
            is_possible_renewal_candidate=data['IsPossibleRenewalCandidate'],
            is_already_renewed=data['IsAlreadyRenewed'],
            product_code=data['ProductCode'],
            sort_order=data['SortOrder'],
            show_on_dashboard=data['ShowOnDashboard'],
            rateplan_code=data['RateplanCode'],
        )