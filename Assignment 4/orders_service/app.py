from decimal import Decimal, InvalidOperation
import re

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from errors import problem
from payment_client import PaymentDeclined, PaymentUnavailable, charge
from store import OrderStore


def amount_to_minor_units(value: object) -> int | None:
    """Accept only positive decimal strings with at most two fractional digits."""
    if not isinstance(value, str) or not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return None
    if amount <= 0 or amount.as_tuple().exponent < -2:
        return None
    minor_units = amount * 100
    return int(minor_units) if minor_units == minor_units.to_integral_value() else None


def validate_order(body: object) -> str | None:
    """Manual JSON validation, replacing the pre-handler XML Schema check in SOAP."""
    if not isinstance(body, dict):
        return "Request body must be a JSON object."
    required = {"userId", "addressId", "items", "cardToken"}
    missing = required - body.keys()
    if missing:
        return f"Missing required field(s): {', '.join(sorted(missing))}."
    unexpected = body.keys() - required
    if unexpected:
        return f"Unexpected field(s): {', '.join(sorted(unexpected))}."
    if not isinstance(body["userId"], int) or isinstance(body["userId"], bool) or body["userId"] < 1:
        return "userId must be a positive integer."
    if not isinstance(body["addressId"], int) or isinstance(body["addressId"], bool) or body["addressId"] < 1:
        return "addressId must be a positive integer."
    if not isinstance(body["cardToken"], str) or not body["cardToken"].strip():
        return "cardToken must be a non-empty string."
    if not isinstance(body["items"], list) or not body["items"]:
        return "items must be a non-empty array."
    for item in body["items"]:
        if not isinstance(item, dict) or set(item) != {"itemId", "quantity", "unitPrice"}:
            return "Each item must contain itemId, quantity, and unitPrice."
        if not isinstance(item["itemId"], int) or isinstance(item["itemId"], bool) or item["itemId"] < 1:
            return "itemId must be a positive integer."
        if not isinstance(item["quantity"], int) or isinstance(item["quantity"], bool) or item["quantity"] < 1:
            return "quantity must be a positive integer."
        if amount_to_minor_units(item["unitPrice"]) is None:
            return "unitPrice must be a positive decimal string with at most two decimal places."
    return None


def validate_cancellation(body: object) -> str | None:
    """Enforces the optional cancellation request body declared by OpenAPI."""
    if body is None:
        return None
    if not isinstance(body, dict):
        return "Cancellation body must be a JSON object."
    if set(body) - {"reason"}:
        return "Cancellation body may contain only reason."
    if "reason" in body and (not isinstance(body["reason"], str) or len(body["reason"]) > 200):
        return "reason must be a string of at most 200 characters."
    return None


def create_app(store: OrderStore | None = None, payment_charge=charge) -> Flask:
    app = Flask(__name__)
    order_store = store or OrderStore()

    @app.errorhandler(BadRequest)
    def malformed_json(_error):
        return problem(400, "Invalid request", "Malformed JSON body.")

    @app.post("/orders")
    def create_order():
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return problem(400, "Invalid request", "Idempotency-Key header is required.")
        if not request.is_json:
            return problem(400, "Invalid request", "Content-Type must be application/json.")
        body = request.get_json()
        validation_error = validate_order(body)
        if validation_error:
            return problem(400, "Invalid request", validation_error)
        existing = order_store.find_by_idempotency_key(idempotency_key)
        if existing:
            response = jsonify(existing.as_json())
            response.status_code = 201
            response.headers["Location"] = f"/orders/{existing.public_id}"
            return response
        total_minor_units = sum(amount_to_minor_units(item["unitPrice"]) * item["quantity"] for item in body["items"])
        try:
            payment_transaction_id = payment_charge(
                order_store.next_public_id, total_minor_units, body["cardToken"], idempotency_key
            )
        except PaymentDeclined as error:
            return problem(422, "Payment declined", str(error))
        except PaymentUnavailable as error:
            return problem(503, "Payment unavailable", str(error))
        order = order_store.create(
            user_id=body["userId"], address_id=body["addressId"], items=body["items"],
            total_minor_units=total_minor_units, status="confirmed", idempotency_key=idempotency_key,
            payment_transaction_id=payment_transaction_id,
        )
        response = jsonify(order.as_json())
        response.status_code = 201
        response.headers["Location"] = f"/orders/{order.public_id}"
        return response

    @app.get("/orders/<order_id>")
    def get_order(order_id: str):
        order = order_store.get(order_id)
        if not order:
            return problem(404, "Order not found", f"No order exists with id {order_id}.")
        return jsonify(order.as_json())

    @app.get("/orders")
    def list_orders():
        raw_user_id = request.args.get("userId")
        if raw_user_id is None or not raw_user_id.isdigit() or int(raw_user_id) < 1:
            return problem(400, "Invalid request", "userId query parameter must be a positive integer.")
        return jsonify({"orders": [order.as_json() for order in order_store.list_for_user(int(raw_user_id))]})

    @app.post("/orders/<order_id>/cancellation")
    def cancel_order(order_id: str):
        if request.data and not request.is_json:
            return problem(400, "Invalid request", "Content-Type must be application/json.")
        body = request.get_json() if request.data else None
        validation_error = validate_cancellation(body)
        if validation_error:
            return problem(400, "Invalid request", validation_error)
        order = order_store.get(order_id)
        if not order:
            return problem(404, "Order not found", f"No order exists with id {order_id}.")
        if order.status == "cancelled":
            return problem(409, "Order state conflict", "A cancelled order cannot be cancelled again.")
        order.status = "cancelled"
        return jsonify(order.as_json())

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=True)
