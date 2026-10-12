

from flask import Flask, jsonify, request


app = Flask(__name__)
charges_by_key: dict[str, str] = {}


@app.post("/charges")
def create_charge():
    body = request.get_json(silent=True)
    key = request.headers.get("Idempotency-Key")
    if not key or not isinstance(body, dict):
        return jsonify({"error": "Invalid charge request."}), 400
    if body.get("cardToken") == "tok_declined":
        return jsonify({"error": "Card declined."}), 402
    if not isinstance(body.get("orderId"), str) or not isinstance(body.get("amountMinorUnits"), int):
        return jsonify({"error": "Invalid charge request."}), 400

    transaction_id = charges_by_key.setdefault(key, f"txn_{len(charges_by_key) + 1:06d}")
    return jsonify({"transactionId": transaction_id}), 201


if __name__ == "__main__":
    app.run(port=5001, debug=True)
