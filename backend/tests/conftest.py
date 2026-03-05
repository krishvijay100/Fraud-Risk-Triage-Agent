"""Shared test helpers."""
from app.models import (
    MockCase, MockCaseCustomer, MockCaseEvent,
    MockCaseSignals, MockCaseHistory, MockCaseLinks,
    MockCaseFreeText, MockCaseLabel,
)


def make_case(
    case_id="T-001",
    alert_type="unusual_transfer",
    country="US",
    amount=100.0,
    avg_amount_30d=100.0,
    new_device=False,
    new_beneficiary=False,
    velocity_1h=1,
    account_age_days=365,
    kyc_level="FULL",
    prior_alerts_90d=0,
    prior_confirmed_fraud=0,
    device_id="D-TEST",
    label="BENIGN",
) -> MockCase:
    return MockCase(
        case_id=case_id,
        alert_type=alert_type,
        created_at="2026-03-03T12:00:00Z",
        customer=MockCaseCustomer(
            customer_id=f"U-{case_id}",
            account_age_days=account_age_days,
            kyc_level=kyc_level,
        ),
        event=MockCaseEvent(amount=amount, currency="USD", channel="card_payment"),
        signals=MockCaseSignals(
            new_device=new_device,
            new_beneficiary=new_beneficiary,
            country=country,
            velocity_1h=velocity_1h,
        ),
        history=MockCaseHistory(
            avg_amount_30d=avg_amount_30d,
            prior_alerts_90d=prior_alerts_90d,
            prior_confirmed_fraud=prior_confirmed_fraud,
        ),
        links=MockCaseLinks(device_id=device_id),
        free_text=MockCaseFreeText(memo="test"),
        label=MockCaseLabel(outcome=label),
    )
