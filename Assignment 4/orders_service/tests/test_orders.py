import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


PAYLOAD = {
    "userId": 7,
    "addressId": 11,
    "cardToken": "tok_demo",
    "items": [{"itemId": 3, "quantity": 2, "unitPrice": "125.50"}],
}


def approved_charge(*_args):
    return "txn_123"


def client():
    return create_app(payment_charge=approved_charge).test_client()


def test_create_returns_201_and_location():
    response = client().post("/orders", json=PAYLOAD, headers={"Idempotency-Key": "key-create"})
    assert response.status_code == 201
    assert response.headers["Location"] == "/orders/ORD-000001"
    assert response.json["status"] == "confirmed"


def test_idempotent_repeat_returns_original_order():
    api = client()
    first = api.post("/orders", json=PAYLOAD, headers={"Idempotency-Key": "key-repeat"})
    repeated = api.post("/orders", json=PAYLOAD, headers={"Idempotency-Key": "key-repeat"})
    assert repeated.status_code == 201
    assert repeated.json == first.json
    assert repeated.headers["Location"] == first.headers["Location"]


def test_malformed_body_returns_single_problem_shape():
    response = client().post("/orders", json={"userId": 7}, headers={"Idempotency-Key": "bad"})
    assert response.status_code == 400
    assert set(response.json) == {"type", "title", "status", "detail"}


def test_unknown_order_returns_404():
    response = client().get("/orders/ORD-999999")
    assert response.status_code == 404
    assert response.json["status"] == 404


def test_cancellation_rejects_undocumented_body_and_second_cancellation_conflicts():
    api = client()
    created = api.post("/orders", json=PAYLOAD, headers={"Idempotency-Key": "key-cancel"})
    order_id = created.json["orderId"]
    invalid = api.post(f"/orders/{order_id}/cancellation", json={"unexpected": True})
    assert invalid.status_code == 400
    assert api.post(f"/orders/{order_id}/cancellation", json={"reason": "Changed plans"}).status_code == 200
    assert api.post(f"/orders/{order_id}/cancellation").status_code == 409
