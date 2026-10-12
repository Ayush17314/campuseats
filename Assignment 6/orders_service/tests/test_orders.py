import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

PAYLOAD = {'userId': 7, 'addressId': 11, 'cardToken': 'tok_demo', 'items': [{'itemId': 3, 'quantity': 2, 'unitPrice': '125.50'}]}
AUTH = {'Authorization': 'Bearer demo-token'}
def approved_charge(*_): return 'txn_123'
def client(): return create_app(payment_charge=approved_charge).test_client()
def post(api, key='key-1', body=PAYLOAD): return api.post('/orders', json=body, headers=AUTH | {'Idempotency-Key': key})

def test_create_idempotency_location_and_headers():
    api = client(); first = post(api); repeat = post(api)
    assert first.status_code == repeat.status_code == 201
    assert first.json == repeat.json and first.headers['Location'] == '/orders/ORD-000001'
    assert first.headers['X-Content-Type-Options'] == 'nosniff'

def test_auth_negotiation_and_failures():
    api = client(); assert api.get('/orders/ORD-1').status_code == 401
    assert api.get('/orders/ORD-1', headers=AUTH | {'Accept': 'text/html'}).status_code == 406
    assert api.post('/orders', json={'userId': 7}, headers=AUTH | {'Idempotency-Key': 'bad'}).status_code == 400
    assert api.get('/orders/ORD-999999', headers=AUTH).status_code == 404

def test_conditional_get_and_write():
    api = client(); made = post(api); oid = made.json['orderId']; read = api.get(f'/orders/{oid}', headers=AUTH); tag = read.headers['ETag']
    assert api.get(f'/orders/{oid}', headers=AUTH | {'If-None-Match': tag}).status_code == 304
    assert api.put(f'/orders/{oid}', json={'addressId': 12, 'items': PAYLOAD['items']}, headers=AUTH | {'If-Match': '"old"'}).status_code == 412
    assert api.put(f'/orders/{oid}', json={'addressId': 12, 'items': PAYLOAD['items']}, headers=AUTH | {'If-Match': tag}).status_code == 200

def test_options_override_and_rate_limit():
    api = client(); assert 'PUT' in api.options('/orders/ORD-000001').headers['Allow']
    oid = post(api).json['orderId']; assert api.post(f'/orders/{oid}', headers=AUTH | {'X-HTTP-Method-Override': 'DELETE'}).status_code == 204
    app = create_app(payment_charge=approved_charge); app.config['RATE_LIMIT'] = 1; limited = app.test_client()
    assert limited.get('/orders/no', headers=AUTH).status_code == 404
    assert limited.get('/orders/no', headers=AUTH).status_code == 429
