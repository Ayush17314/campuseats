"""Local CampusEats Payments service used to demonstrate the Orders HTTP call."""

from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)
    charges_by_key: dict[str, dict] = {}
    next_transaction = 1

    @app.post("/charges")
    def create_charge():
        nonlocal next_transaction
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 400
        key = request.headers.get("Idempotency-Key")
        body = request.get_json()
        required = {"orderId", "amountMinorUnits", "cardToken"}
        if not key or not isinstance(body, dict) or set(body) != required:
            return jsonify({"error": "A valid body and Idempotency-Key are required."}), 400
        if key in charges_by_key:
            return jsonify(charges_by_key[key]), 201
        if body["cardToken"] == "tok_declined":
            return jsonify({"error": "card declined"}), 402
        transaction = {
            "transactionId": f"txn_{next_transaction:06d}",
            "orderId": body["orderId"],
            "status": "approved",
            "chargedAmountMinorUnits": body["amountMinorUnits"],
        }
        next_transaction += 1
        charges_by_key[key] = transaction
        return jsonify(transaction), 201

    return app


if __name__ == "__main__":
    create_app().run(port=5001, debug=True)
