from decimal import Decimal, InvalidOperation
from hashlib import sha256
import gzip
import json
import logging
import re
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest, MethodNotAllowed
from errors import problem, xml_response
from payment_client import PaymentDeclined, PaymentUnavailable, charge
from store import OrderStore

log = logging.getLogger(__name__)
UNAVAILABLE_ITEM_IDS = {999}


def amount_to_minor_units(value: object) -> int | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return None
    return int(amount * 100) if amount > 0 and amount.as_tuple().exponent >= -2 else None


def _validate_items(items: object, present: bool, errors: list[dict[str, str]]) -> None:
    if not present:
        return
    if isinstance(items, list) and not items:
        errors.append({'field': 'items', 'message': 'Cart must contain at least one item.'})
    elif not isinstance(items, list):
        errors.append({'field': 'items', 'message': 'Must be an array.'})
    else:
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({'field': f'items[{i}]', 'message': 'Must be an object.'})
                continue
            for key in ('itemId', 'quantity', 'unitPrice'):
                if key not in item:
                    errors.append({'field': f'items[{i}].{key}', 'message': 'This field is required.'})
            for extra in sorted(set(item) - {'itemId', 'quantity', 'unitPrice'}):
                errors.append({'field': f'items[{i}].{extra}', 'message': 'Unexpected field.'})
            for key in ('itemId', 'quantity'):
                v = item.get(key)
                if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 1):
                    errors.append({'field': f'items[{i}].{key}', 'message': 'Must be an integer greater than or equal to 1.'})
            p = item.get('unitPrice')
            if p is not None and amount_to_minor_units(p) is None:
                errors.append({'field': f'items[{i}].unitPrice', 'message': 'Must be a positive decimal string with at most two decimal places.'})


def validate(body: object) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(body, dict):
        return [{'field': 'body', 'message': 'Must be a JSON object.'}]
    required = ('userId', 'addressId', 'items', 'cardToken')
    for key in required:
        if key not in body:
            errors.append({'field': key, 'message': 'This field is required.'})
    for extra in sorted(set(body) - set(required)):
        errors.append({'field': extra, 'message': 'Unexpected field.'})
    for key in ('userId', 'addressId'):
        if key in body and (not isinstance(body[key], int) or isinstance(body[key], bool) or body[key] < 1):
            errors.append({'field': key, 'message': 'Must be a positive integer.'})
    if 'cardToken' in body and (not isinstance(body['cardToken'], str) or not body['cardToken'].strip()):
        errors.append({'field': 'cardToken', 'message': 'Must be a non-empty string.'})
    _validate_items(body.get('items'), 'items' in body, errors)
    return errors


def validate_replacement(body: object) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(body, dict):
        return [{'field': 'body', 'message': 'Must be a JSON object.'}]
    for key in ('addressId', 'items'):
        if key not in body:
            errors.append({'field': key, 'message': 'This field is required.'})
    for extra in sorted(set(body) - {'addressId', 'items'}):
        errors.append({'field': extra, 'message': 'Unexpected field.'})
    if 'addressId' in body and (not isinstance(body['addressId'], int) or isinstance(body['addressId'], bool) or body['addressId'] < 1):
        errors.append({'field': 'addressId', 'message': 'Must be a positive integer.'})
    _validate_items(body.get('items'), 'items' in body, errors)
    return errors


def etag(order) -> str:
    payload = json.dumps(order.as_json(), sort_keys=True, separators=(',', ':')).encode('utf-8')
    return '"' + sha256(payload).hexdigest() + '"'


def wants_xml() -> bool:
    accept = request.headers.get('Accept', '*/*')
    tokens = [part.strip().split(';')[0].strip() for part in accept.split(',') if part.strip()]
    return 'application/xml' in tokens and 'application/json' not in tokens


def negotiate_response(status: int, data: dict[str, object]) -> Response:
    if wants_xml():
        return xml_response(status, data)
    response = jsonify(data)
    response.status_code = status
    response.content_type = 'application/json; charset=utf-8'
    return response


def create_app(store: OrderStore | None = None, payment_charge=charge) -> Flask:
    app = Flask(__name__)
    s = store or OrderStore()
    app.config.setdefault('RATE_LIMIT', 100)
    app.config['RATE_COUNTS'] = {}

    @app.before_request
    def auth_and_limit():
        if request.method == 'OPTIONS':
            return None
        accept = request.headers.get('Accept', '*/*')
        accepted_types = [a.strip().split(';')[0].strip() for a in accept.split(',') if a.strip()]
        if not any(t in ('*/*', 'application/*', 'application/json', 'application/xml') for t in accepted_types):
            return problem(406, 'about:blank', 'Not Acceptable', 'Supported representations are application/json and application/xml.')
        token = request.headers.get('Authorization', '')
        if not token.startswith('Bearer ') or not token[7:].strip():
            return problem(401, 'about:blank', 'Unauthorized', 'Authorization: Bearer token is required.')
        client = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
        counts = app.config['RATE_COUNTS']
        n = counts.get(client, 0)
        if n >= app.config['RATE_LIMIT']:
            return problem(429, 'about:blank', 'Too Many Requests', 'Request limit exceeded; retry later.', retry_after=60)
        counts[client] = n + 1

    @app.after_request
    def headers(r: Response) -> Response:
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
        r.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Idempotency-Key, If-None-Match, If-Match, X-HTTP-Method-Override'
        r.headers['X-Content-Type-Options'] = 'nosniff'
        r.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        client = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
        limit = app.config['RATE_LIMIT']
        r.headers['X-RateLimit-Limit'] = str(limit)
        r.headers['X-RateLimit-Remaining'] = str(max(0, limit - app.config['RATE_COUNTS'].get(client, 0)))
        if r.status_code not in (204, 304) and r.get_data():
            ct = r.headers.get('Content-Type', '')
            if ct.startswith('application/problem+json'):
                r.content_type = 'application/problem+json; charset=utf-8'
            elif ct.startswith('application/xml'):
                r.content_type = 'application/xml; charset=utf-8'
            else:
                r.content_type = 'application/json; charset=utf-8'
            if 'gzip' in request.headers.get('Accept-Encoding', '').lower() and len(r.get_data()) >= 200:
                r.set_data(gzip.compress(r.get_data()))
                r.headers['Content-Encoding'] = 'gzip'
                r.headers['Vary'] = 'Accept-Encoding'
        return r

    @app.errorhandler(BadRequest)
    def malformed(_):
        return problem(400, 'about:blank', 'Bad Request', 'Malformed JSON body.')

    @app.errorhandler(404)
    def route_missing(_):
        return problem(404, 'https://campuseats.example/problems/order-not-found', 'Not Found', 'No endpoint or order exists at this path.')

    @app.errorhandler(405)
    def method_missing(err: MethodNotAllowed):
        r = problem(405, 'about:blank', 'Method Not Allowed', 'This HTTP method is not supported for the resource.')
        if getattr(err, 'valid_methods', None):
            r.headers['Allow'] = ', '.join(err.valid_methods)
        return r

    @app.errorhandler(Exception)
    def unexpected_error(_):
        log.exception('Unhandled internal exception in Orders service')
        return problem(500, 'about:blank', 'Internal Server Error', 'An unexpected internal error occurred.')

    @app.route('/orders', methods=['OPTIONS'])
    @app.route('/orders/<oid>', methods=['OPTIONS'])
    def options(oid: str | None = None) -> Response:
        r = Response(status=204)
        r.headers['Allow'] = 'GET, POST, OPTIONS' if oid is None else 'GET, PATCH, PUT, DELETE, POST, OPTIONS'
        return r

    @app.post('/orders')
    def create():
        key = request.headers.get('Idempotency-Key')
        if not key or not key.strip():
            return problem(400, 'about:blank', 'Bad Request', 'Idempotency-Key header is required.')
        if not request.is_json:
            return problem(400, 'about:blank', 'Bad Request', 'Content-Type must be application/json.')
        body = request.get_json()
        errors = validate(body)
        if errors:
            only_empty_cart = len(errors) == 1 and errors[0]['field'] == 'items' and 'at least one' in errors[0]['message']
            problem_type = 'https://campuseats.example/problems/empty-cart' if only_empty_cart else 'https://campuseats.example/problems/validation-error'
            return problem(422, problem_type, 'Validation Failed', 'Request fields are invalid.', errors)
        if any(i['itemId'] in UNAVAILABLE_ITEM_IDS for i in body['items']):
            return problem(422, 'https://campuseats.example/problems/item-unavailable', 'Item Unavailable', 'One or more requested items are currently unavailable.')
        old = s.find_by_idempotency_key(key)
        if old:
            r = negotiate_response(201, old.as_json())
            r.headers['Location'] = f'/orders/{old.public_id}'
            return r
        total = sum(amount_to_minor_units(i['unitPrice']) * i['quantity'] for i in body['items'])
        try:
            txn = payment_charge(s.next_public_id, total, body['cardToken'], key)
        except PaymentDeclined as e:
            log.warning('payment declined for key=%s: %s', key, e)
            return problem(422, 'https://campuseats.example/problems/payment-declined', 'Payment Declined', 'Payment could not be approved.')
        except PaymentUnavailable as e:
            log.error('payments unavailable for key=%s: %s', key, e)
            return problem(503, 'https://campuseats.example/problems/payment-unavailable', 'Payment Unavailable', 'Payment service is temporarily unavailable.', retry_after=30)
        except Exception:
            log.exception('unexpected payment failure for key=%s', key)
            return problem(503, 'https://campuseats.example/problems/payment-unavailable', 'Payment Unavailable', 'Order could not be processed temporarily.', retry_after=30)
        o = s.create(
            user_id=body['userId'],
            address_id=body['addressId'],
            items=body['items'],
            total_minor_units=total,
            status='confirmed',
            idempotency_key=key,
            payment_transaction_id=txn,
        )
        r = negotiate_response(201, o.as_json())
        r.headers['Location'] = f'/orders/{o.public_id}'
        return r

    @app.get('/orders')
    def listing():
        raw = request.args.get('userId', '')
        if not raw.isdigit() or int(raw) < 1:
            return problem(400, 'about:blank', 'Bad Request', 'userId query parameter must be a positive integer.')
        orders = s.list_for_user(int(raw))
        status = request.args.get('status')
        if status:
            orders = [o for o in orders if o.status == status]
        sort = request.args.get('sort', 'orderId')
        reverse = request.args.get('direction', 'asc') == 'desc'
        if sort not in ('orderId', 'totalAmount'):
            return problem(400, 'about:blank', 'Bad Request', 'sort must be orderId or totalAmount.')
        orders.sort(key=lambda o: o.public_id if sort == 'orderId' else o.total_minor_units, reverse=reverse)
        try:
            page = int(request.args.get('page', 1))
            size = int(request.args.get('pageSize', 20))
        except ValueError:
            return problem(400, 'about:blank', 'Bad Request', 'page and pageSize must be integers.')
        if page < 1 or not 1 <= size <= 100:
            return problem(400, 'about:blank', 'Bad Request', 'page must be positive and pageSize must be 1..100.')
        start = (page - 1) * size
        data = {
            'orders': [o.as_json() for o in orders[start:start + size]],
            'page': page,
            'pageSize': size,
            'total': len(orders),
        }
        return negotiate_response(200, data)

    @app.get('/orders/<oid>')
    def get(oid: str):
        o = s.get(oid)
        if not o:
            return problem(404, 'https://campuseats.example/problems/order-not-found', 'Order Not Found', 'No order exists with the requested id.')
        tag = etag(o)
        if request.headers.get('If-None-Match', '').strip('"') == tag.strip('"'):
            r = Response(status=304)
            r.headers['ETag'] = tag
            r.headers['Cache-Control'] = 'private, max-age=60'
            return r
        r = negotiate_response(200, o.as_json())
        r.headers['ETag'] = tag
        r.headers['Cache-Control'] = 'private, max-age=60'
        return r

    @app.route('/orders/<oid>', methods=['PATCH', 'PUT', 'DELETE', 'POST'])
    def mutate(oid: str):
        method = request.headers.get('X-HTTP-Method-Override', request.method).upper() if request.method == 'POST' else request.method
        if method not in ('PATCH', 'PUT', 'DELETE'):
            r = problem(405, 'about:blank', 'Method Not Allowed', 'POST here requires X-HTTP-Method-Override: PATCH, PUT, or DELETE.')
            r.headers['Allow'] = 'GET, PATCH, PUT, DELETE, POST, OPTIONS'
            return r
        o = s.get(oid)
        if not o:
            return problem(404, 'https://campuseats.example/problems/order-not-found', 'Order Not Found', 'No order exists with the requested id.')
        if method == 'DELETE':
            s.delete(oid)
            return Response(status=204)
        if o.status == 'cancelled':
            return problem(409, 'https://campuseats.example/problems/illegal-transition', 'Illegal Transition', 'A cancelled order cannot be modified.')
        if not request.headers.get('If-Match'):
            return problem(428, 'about:blank', 'Precondition Required', 'If-Match header is required.')
        if request.headers['If-Match'] != etag(o):
            return problem(412, 'about:blank', 'Precondition Failed', 'ETag does not match current order.')
        if not request.is_json:
            return problem(400, 'about:blank', 'Bad Request', 'Content-Type must be application/json.')
        b = request.get_json()
        errors = validate_replacement(b)
        if errors:
            only_empty_cart = len(errors) == 1 and errors[0]['field'] == 'items' and 'at least one' in errors[0]['message']
            problem_type = 'https://campuseats.example/problems/empty-cart' if only_empty_cart else 'https://campuseats.example/problems/validation-error'
            return problem(422, problem_type, 'Validation Failed', 'Request fields are invalid.', errors)
        if any(i['itemId'] in UNAVAILABLE_ITEM_IDS for i in b['items']):
            return problem(422, 'https://campuseats.example/problems/item-unavailable', 'Item Unavailable', 'One or more requested items are currently unavailable.')
        o.address_id = b['addressId']
        o.items = b['items']
        o.total_minor_units = sum(amount_to_minor_units(i['unitPrice']) * i['quantity'] for i in b['items'])
        r = negotiate_response(200, o.as_json())
        r.headers['ETag'] = etag(o)
        r.headers['Cache-Control'] = 'no-store'
        return r

    @app.post('/orders/<oid>/cancellation')
    def cancel(oid: str):
        if request.data and not request.is_json:
            return problem(400, 'about:blank', 'Bad Request', 'Content-Type must be application/json.')
        o = s.get(oid)
        if not o:
            return problem(404, 'https://campuseats.example/problems/order-not-found', 'Order Not Found', 'No order exists with the requested id.')
        if o.status == 'cancelled':
            return problem(409, 'https://campuseats.example/problems/illegal-transition', 'Illegal Transition', 'A cancelled order cannot be cancelled again.')
        o.status = 'cancelled'
        r = negotiate_response(200, o.as_json())
        r.headers['Cache-Control'] = 'no-store'
        return r

    return app


if __name__ == '__main__':
    create_app().run(port=5000)
