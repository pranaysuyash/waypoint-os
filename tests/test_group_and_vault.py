from spine_api.services.group_payments import (
    GroupPaymentSplit,
    create_group_payment_split,
    record_traveler_payment,
)
from spine_api.services.card_vault import (
    CardAuthorizationAgreement,
    create_card_authorization_record,
)


def test_group_payment_equal_split_and_payments():
    travelers = [
        {"name": "Alice Smith", "email": "alice@example.com"},
        {"name": "Bob Jones", "email": "bob@example.com"},
        {"name": "Charlie Brown", "email": "charlie@example.com"},
    ]

    split: GroupPaymentSplit = create_group_payment_split(
        trip_id="trip_group_01",
        total_package_usd=3000.0,
        travelers=travelers,
    )

    assert len(split.shares) == 3
    assert split.shares[0].share_amount_usd == 1000.0
    assert split.shares[1].share_amount_usd == 1000.0
    assert split.shares[2].share_amount_usd == 1000.0
    assert split.all_settled is False

    # Pay first share
    token1 = split.shares[0].payment_link_token
    split = record_traveler_payment(split, token1, 1000.0)
    assert split.shares[0].status == "paid"
    assert split.total_paid_usd == 1000.0
    assert split.outstanding_balance_usd == 2000.0
    assert split.all_settled is False

    # Pay remaining shares
    token2 = split.shares[1].payment_link_token
    token3 = split.shares[2].payment_link_token
    split = record_traveler_payment(split, token2, 1000.0)
    split = record_traveler_payment(split, token3, 1000.0)

    assert split.total_paid_usd == 3000.0
    assert split.outstanding_balance_usd == 0.0
    assert split.all_settled is True


def test_card_vault_authorization_record():
    auth: CardAuthorizationAgreement = create_card_authorization_record(
        trip_id="trip_luxury_99",
        traveler_name="Rajesh Sharma",
        traveler_email="rajesh@example.com",
        card_brand="Visa",
        card_last4="4242",
        card_token="pm_tok_test_stripe_999",
        authorized_max_amount_usd=5000.0,
        client_ip_address="192.0.2.1",
    )

    assert auth.authorization_id.startswith("cauth_")
    assert auth.card_last4 == "4242"
    assert auth.card_token == "pm_tok_test_stripe_999"
    assert len(auth.agreement_hash) == 64
    assert auth.status == "active"
