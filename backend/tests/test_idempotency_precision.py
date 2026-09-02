"""Tests for Integer-Paise Precision and Float Drift Resilience in Idempotency Keys."""

import uuid
import pytest
from app.services.idempotency_service import idempotency_service


def test_float_drift_produces_identical_idempotency_key():
    """Verify that 0.1 + 0.2 float drift (0.30000000000000004) produces the exact same hash as 0.30."""
    conv_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    prod_id = uuid.uuid4()

    # Float drift total: 0.1 + 0.2 = 0.30000000000000004
    drift_total = 0.1 + 0.2
    exact_total = 0.30

    items_drift = [{"product_id": str(prod_id), "quantity": 1, "price": 0.1 + 0.2}]
    items_exact = [{"product_id": str(prod_id), "quantity": 1, "price": 0.30}]

    key_drift = idempotency_service.generate_checkout_key(conv_id, merchant_id, items_drift, drift_total)
    key_exact = idempotency_service.generate_checkout_key(conv_id, merchant_id, items_exact, exact_total)

    assert key_drift == key_exact, f"Float drift produced mismatch: {key_drift} vs {key_exact}"
    assert key_drift.startswith("idemp_ord_")


def test_item_order_permutation_invariance():
    """Verify that permutations of item list order produce the same deterministic key."""
    conv_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    prod_a = uuid.uuid4()
    prod_b = uuid.uuid4()

    items_1 = [
        {"product_id": str(prod_a), "quantity": 2, "price": 150.0},
        {"product_id": str(prod_b), "quantity": 1, "price": 400.0},
    ]
    items_2 = [
        {"product_id": str(prod_b), "quantity": 1, "price": 400.0},
        {"product_id": str(prod_a), "quantity": 2, "price": 150.0},
    ]

    key_1 = idempotency_service.generate_checkout_key(conv_id, merchant_id, items_1, 700.0)
    key_2 = idempotency_service.generate_checkout_key(conv_id, merchant_id, items_2, 700.0)

    assert key_1 == key_2, "Item list sorting failed to ensure permutation invariance"
