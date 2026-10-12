from decimal import Decimal, InvalidOperation
from hashlib import sha256
import gzip
import json
import re
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest
from errors import problem
from payment_client import PaymentDeclined, PaymentUnavailable, charge
from store import OrderStore


def amount_to_minor_units(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+(\.\d{1,2})?", value): return None
    try: amount = Decimal(value)
    except InvalidOperation: return None
    return int(amount * 100) if amount > 0 and amount.as_tuple().exponent >= -2 else None


def validate_order(body):
    if not isinstance(body, dict): return 'Request body must be a JSON object.'
    required = {'userId', 'addressId', 'items', 'cardToken'}
    if required - body.keys(): return f"Missing required field(s): {', '.join(sorted(required - body.keys()))}."
    if body.keys() - required: return f"Unexpected field(s): {', '.join(sorted(body.keys() - required))}."
    if not isinstance(body['userId'], int) or isinstance(body['userId'], bool) or body['userId'] < 1: return 'userId must be a positive integer.'
    if not isinstance(body['addressId'], int) or isinstance(body['addressId'], bool) or body['addressId'] < 1: return 'addressId must be a positive integer.'
    if not isinstance(body['cardToken'], str) or not body['cardToken'].strip(): return 'cardToken must be a non-empty string.'
    if not isinstance(body['items'], list) or not body['items']: return 'items must be a non-empty array.'
    for item in body['items']:
        if not isinstance(item, dict) or set(item) != {'itemId', 'quantity', 'unitPrice'}: return 'Each item must contain itemId, quantity, and unitPrice.'
        if not isinstance(item['itemId'], int) or isinstance(item['itemId'], bool) or item['itemId'] < 1: return 'itemId must be a positive integer.'
        if not isinstance(item['quantity'], int) or isinstance(item['quantity'], bool) or item['quantity'] < 1: return 'quantity must be a positive integer.'
        if amount_to_minor_units(item['unitPrice']) is None: return 'unitPrice must be a positive decimal string with at most two decimal places.'
    return None


def etag(order): return '"' + sha256(json.dumps(order.as_json(), sort_keys=True, separators=(',', ':')).encode()).hexdigest() + '"'


def create_app(store=None, payment_charge=charge):
    app = Flask(__name__); order_store = store or OrderStore(); app.config.setdefault('RATE_LIMIT', 100); app.config['RATE_COUNTS'] = {}
    @app.before_request
    def protocol():
        if request.method == 'OPTIONS': return None
        if not any(x.strip().split(';')[0] in ('*/*', 'application/json') for x in request.headers.get('Accept', '*/*').split(',')): return problem(406, 'Not acceptable', 'Only application/json is available.')
        token = request.headers.get('Authorization', '')
        if not token.startswith('Bearer ') or not token[7:].strip(): return problem(401, 'Unauthorized', 'Authorization: Bearer <token> is required.')
        client = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip(); counts = app.config['RATE_COUNTS']; used = counts.get(client, 0)
        if used >= app.config['RATE_LIMIT']:
            response = problem(429, 'Too many requests', 'Per-client request budget exceeded.'); response.headers['Retry-After'] = '60'; return response
        counts[client] = used + 1
    @app.after_request
    def headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'; response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Idempotency-Key, If-None-Match, If-Match, X-HTTP-Method-Override'; response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'; response.headers['X-Content-Type-Options'] = 'nosniff'; response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        client = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip(); limit = app.config['RATE_LIMIT']; response.headers['X-RateLimit-Limit'] = str(limit); response.headers['X-RateLimit-Remaining'] = str(max(0, limit - app.config['RATE_COUNTS'].get(client, 0)))
        if response.status_code != 304 and response.get_data() and response.mimetype in ('application/json', 'application/problem+json'):
            response.content_type = 'application/json'
            if 'gzip' in request.headers.get('Accept-Encoding', '').lower() and len(response.get_data()) >= 200: response.set_data(gzip.compress(response.get_data())); response.headers['Content-Encoding'] = 'gzip'; response.headers['Vary'] = 'Accept-Encoding'
        return response
    @app.errorhandler(BadRequest)
    def bad_json(_): return problem(400, 'Invalid request', 'Malformed JSON body.')
    @app.route('/orders', methods=['OPTIONS'])
    @app.route('/orders/<order_id>', methods=['OPTIONS'])
    def options(order_id=None):
        response = Response(status=204); response.headers['Allow'] = 'GET, POST, PUT, DELETE, OPTIONS' if order_id else 'GET, POST, OPTIONS'; return response
    @app.post('/orders')
    def create_order():
        key = request.headers.get('Idempotency-Key')
        if not key: return problem(400, 'Invalid request', 'Idempotency-Key header is required.')
        if not request.is_json: return problem(400, 'Invalid request', 'Content-Type must be application/json.')
        body = request.get_json(); error = validate_order(body)
        if error: return problem(400, 'Invalid request', error)
        existing = order_store.find_by_idempotency_key(key)
        if existing:
            response = jsonify(existing.as_json()); response.status_code = 201; response.headers['Location'] = f'/orders/{existing.public_id}'; return response
        total = sum(amount_to_minor_units(i['unitPrice']) * i['quantity'] for i in body['items'])
        try: transaction = payment_charge(order_store.next_public_id, total, body['cardToken'], key)
        except PaymentDeclined as error: return problem(422, 'Payment declined', str(error))
        except PaymentUnavailable as error: return problem(503, 'Payment unavailable', str(error))
        order = order_store.create(user_id=body['userId'], address_id=body['addressId'], items=body['items'], total_minor_units=total, status='confirmed', idempotency_key=key, payment_transaction_id=transaction)
        response = jsonify(order.as_json()); response.status_code = 201; response.headers['Location'] = f'/orders/{order.public_id}'; return response
    @app.get('/orders')
    def list_orders():
        raw = request.args.get('userId')
        if raw is None or not raw.isdigit() or int(raw) < 1: return problem(400, 'Invalid request', 'userId query parameter must be a positive integer.')
        orders = order_store.list_for_user(int(raw)); status = request.args.get('status')
        if status: orders = [o for o in orders if o.status == status]
        sort = request.args.get('sort', 'orderId'); reverse = request.args.get('direction', 'asc') == 'desc'
        if sort not in ('orderId', 'totalAmount'): return problem(400, 'Invalid request', 'sort must be orderId or totalAmount.')
        orders.sort(key=lambda o: o.public_id if sort == 'orderId' else o.total_minor_units, reverse=reverse)
        try: page, size = int(request.args.get('page', 1)), int(request.args.get('pageSize', 20))
        except ValueError: return problem(400, 'Invalid request', 'page and pageSize must be integers.')
        if page < 1 or not 1 <= size <= 100: return problem(400, 'Invalid request', 'page must be positive and pageSize must be 1..100.')
        start = (page - 1) * size; return jsonify({'orders': [o.as_json() for o in orders[start:start + size]], 'page': page, 'pageSize': size, 'total': len(orders)})
    @app.get('/orders/<order_id>')
    def get_order(order_id):
        order = order_store.get(order_id)
        if not order: return problem(404, 'Order not found', f'No order exists with id {order_id}.')
        tag = etag(order)
        if request.headers.get('If-None-Match', '').strip('"') == tag.strip('"'):
            response = Response(status=304); response.headers['ETag'] = tag; response.headers['Cache-Control'] = 'private, max-age=60'; return response
        response = jsonify(order.as_json()); response.headers['ETag'] = tag; response.headers['Cache-Control'] = 'private, max-age=60'; return response
    @app.route('/orders/<order_id>', methods=['PUT', 'DELETE', 'POST'])
    def mutate(order_id):
        method = request.headers.get('X-HTTP-Method-Override', request.method).upper() if request.method == 'POST' else request.method; order = order_store.get(order_id)
        if method not in ('PUT', 'DELETE'): return problem(405, 'Method not allowed', 'POST here requires X-HTTP-Method-Override: PUT or DELETE.')
        if not order: return problem(404, 'Order not found', f'No order exists with id {order_id}.')
        if method == 'DELETE': order_store.delete(order_id); return Response(status=204)
        if not request.is_json: return problem(400, 'Invalid request', 'Content-Type must be application/json.')
        if not request.headers.get('If-Match'): return problem(428, 'Precondition required', 'If-Match is required for replacement.')
        if request.headers['If-Match'] != etag(order): return problem(412, 'Precondition failed', 'The order changed; retrieve its current ETag before retrying.')
        body = request.get_json()
        if not isinstance(body, dict) or set(body) != {'addressId', 'items'}: return problem(400, 'Invalid request', 'A replacement must contain exactly addressId and items.')
        error = validate_order({'userId': 1, 'addressId': body['addressId'], 'items': body['items'], 'cardToken': 'not-used'})
        if error: return problem(400, 'Invalid request', error)
        order.address_id, order.items = body['addressId'], body['items']; order.total_minor_units = sum(amount_to_minor_units(i['unitPrice']) * i['quantity'] for i in body['items'])
        response = jsonify(order.as_json()); response.headers['ETag'] = etag(order); response.headers['Cache-Control'] = 'no-store'; return response
    @app.post('/orders/<order_id>/cancellation')
    def cancel(order_id):
        if request.data and not request.is_json: return problem(400, 'Invalid request', 'Content-Type must be application/json.')
        order = order_store.get(order_id)
        if not order: return problem(404, 'Order not found', f'No order exists with id {order_id}.')
        if order.status == 'cancelled': return problem(409, 'Order state conflict', 'A cancelled order cannot be cancelled again.')
        order.status = 'cancelled'; response = jsonify(order.as_json()); response.headers['Cache-Control'] = 'no-store'; return response
    return app


if __name__ == '__main__': create_app().run(port=5000, debug=True)
