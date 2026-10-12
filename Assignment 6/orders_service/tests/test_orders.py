import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from payment_client import PaymentDeclined, PaymentUnavailable

PAYLOAD = {'userId': 7, 'addressId': 11, 'cardToken': 'tok_demo', 'items': [{'itemId': 3, 'quantity': 2, 'unitPrice': '125.50'}]}
AUTH = {'Authorization': 'Bearer demo-token'}


def approved_charge(*_):
    return 'txn_123'


def client(payment_fn=approved_charge):
    return create_app(payment_charge=payment_fn).test_client()


def post(api, key='key-1', body=PAYLOAD, extra_headers=None):
    headers = AUTH | {'Idempotency-Key': key}
    if extra_headers:
        headers |= extra_headers
    return api.post('/orders', json=body, headers=headers)


def test_create_idempotency_location_and_headers():
    api = client()
    first = post(api)
    repeat = post(api)
    assert first.status_code == repeat.status_code == 201
    assert first.json == repeat.json and first.headers['Location'] == '/orders/ORD-000001'
    assert first.headers['Content-Type'] == 'application/json; charset=utf-8'
    assert first.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'Strict-Transport-Security' in first.headers
    assert 'X-RateLimit-Limit' in first.headers and 'X-RateLimit-Remaining' in first.headers


def test_auth_negotiation_and_failures():
    api = client()
    unauth = api.get('/orders/ORD-1')
    assert unauth.status_code == 401
    assert unauth.headers['Content-Type'] == 'application/problem+json; charset=utf-8'
    assert api.get('/orders/ORD-1', headers={'Authorization': 'Bearer    '}).status_code == 401

    not_acceptable = api.get('/orders/ORD-1', headers=AUTH | {'Accept': 'text/html'})
    assert not_acceptable.status_code == 406
    assert not_acceptable.headers['Content-Type'] == 'application/problem+json; charset=utf-8'

    malformed = api.post('/orders', data='{bad json', content_type='application/json', headers=AUTH | {'Idempotency-Key': 'bad-json'})
    assert malformed.status_code == 400
    assert malformed.json['status'] == 400

    missing_fields = api.post('/orders', json={'userId': 7}, headers=AUTH | {'Idempotency-Key': 'bad-fields'})
    assert missing_fields.status_code == 422
    assert missing_fields.json['type'] == 'https://campuseats.example/problems/validation-error'
    assert len(missing_fields.json['errors']) == 3

    not_found = api.get('/orders/ORD-999999', headers=AUTH)
    assert not_found.status_code == 404
    assert not_found.json['type'] == 'https://campuseats.example/problems/order-not-found'


def test_validation_empty_cart_multi_field_and_item_unavailable():
    api = client()
    empty = post(api, key='empty', body=PAYLOAD | {'items': []})
    assert empty.status_code == 422
    assert empty.json['type'] == 'https://campuseats.example/problems/empty-cart'
    assert empty.json['errors'] == [{'field': 'items', 'message': 'Cart must contain at least one item.'}]

    multi = post(api, key='multi', body={'userId': 0, 'addressId': 0, 'cardToken': 'tok_demo', 'items': [{'itemId': 3, 'quantity': 0, 'unitPrice': '125.50'}]})
    assert multi.status_code == 422
    assert multi.json['type'] == 'https://campuseats.example/problems/validation-error'
    fields = [e['field'] for e in multi.json['errors']]
    assert fields == ['userId', 'addressId', 'items[0].quantity']

    unavail = post(api, key='unavail', body=PAYLOAD | {'items': [{'itemId': 999, 'quantity': 1, 'unitPrice': '50.00'}]})
    assert unavail.status_code == 422
    assert unavail.json['type'] == 'https://campuseats.example/problems/item-unavailable'


def test_payment_declined_unavailable_and_no_internal_leak():
    def declined_charge(*_):
        raise PaymentDeclined('Card declined by issuer')

    def unavailable_charge(*_):
        raise PaymentUnavailable('Connection timed out')

    def crashing_charge(*_):
        raise RuntimeError('postgres://secret-internal-dsn-failure')

    api_declined = client(declined_charge)
    res_declined = post(api_declined, key='k-dec')
    assert res_declined.status_code == 422
    assert res_declined.json['type'] == 'https://campuseats.example/problems/payment-declined'

    api_unavail = client(unavailable_charge)
    res_unavail = post(api_unavail, key='k-unavail')
    assert res_unavail.status_code == 503
    assert res_unavail.headers['Retry-After'] == '30'
    assert res_unavail.json['type'] == 'https://campuseats.example/problems/payment-unavailable'

    api_crash = client(crashing_charge)
    res_crash = post(api_crash, key='k-crash')
    assert res_crash.status_code == 503
    assert res_crash.headers['Retry-After'] == '30'
    assert 'postgres://' not in res_crash.get_data(as_text=True)


def test_cancellation_and_illegal_transition():
    api = client()
    oid = post(api).json['orderId']
    first_cancel = api.post(f'/orders/{oid}/cancellation', headers=AUTH)
    assert first_cancel.status_code == 200
    assert first_cancel.json['status'] == 'cancelled'

    second_cancel = api.post(f'/orders/{oid}/cancellation', headers=AUTH)
    assert second_cancel.status_code == 409
    assert second_cancel.json['type'] == 'https://campuseats.example/problems/illegal-transition'


def test_xml_content_negotiation():
    api = client()
    oid = post(api).json['orderId']
    xml_one = api.get(f'/orders/{oid}', headers=AUTH | {'Accept': 'application/xml'})
    assert xml_one.status_code == 200
    assert xml_one.headers['Content-Type'] == 'application/xml; charset=utf-8'
    text_one = xml_one.get_data(as_text=True)
    assert '<order><orderId>ORD-000001</orderId>' in text_one
    assert '<items><item><itemId>3</itemId><quantity>2</quantity><unitPrice>125.50</unitPrice></item></items>' in text_one

    xml_list = api.get('/orders?userId=7', headers=AUTH | {'Accept': 'application/xml'})
    assert xml_list.status_code == 200
    assert xml_list.headers['Content-Type'] == 'application/xml; charset=utf-8'
    assert '<orders><order><orderId>ORD-000001</orderId>' in xml_list.get_data(as_text=True)


def test_conditional_get_and_write():
    api = client()
    made = post(api)
    oid = made.json['orderId']
    read = api.get(f'/orders/{oid}', headers=AUTH)
    tag = read.headers['ETag']
    assert api.get(f'/orders/{oid}', headers=AUTH | {'If-None-Match': tag}).status_code == 304
    assert api.put(f'/orders/{oid}', json={'addressId': 12, 'items': PAYLOAD['items']}, headers=AUTH | {'If-Match': '"old"'}).status_code == 412
    assert api.patch(f'/orders/{oid}', json={'addressId': 12, 'items': PAYLOAD['items']}, headers=AUTH | {'If-Match': tag}).status_code == 200


def test_options_override_and_rate_limit():
    api = client()
    assert 'PUT' in api.options('/orders/ORD-000001').headers['Allow']
    oid = post(api).json['orderId']
    assert api.post(f'/orders/{oid}', headers=AUTH | {'X-HTTP-Method-Override': 'DELETE'}).status_code == 204
    app = create_app(payment_charge=approved_charge)
    app.config['RATE_LIMIT'] = 1
    limited = app.test_client()
    assert limited.get('/orders/no', headers=AUTH).status_code == 404
    res_429 = limited.get('/orders/no', headers=AUTH)
    assert res_429.status_code == 429
    assert res_429.headers['Retry-After'] == '60'
