from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json, logging, re
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest
from errors import problem, xml_response
from payment_client import PaymentDeclined, PaymentUnavailable, charge
from store import OrderStore
log = logging.getLogger(__name__)

def etag(order): return '"' + sha256(json.dumps(order.as_json(), sort_keys=True, separators=(',', ':')).encode()).hexdigest() + '"'
def validate(body):
    errors=[]
    if not isinstance(body,dict): return [{'field':'body','message':'Must be a JSON object.'}]
    for key in ('userId','addressId','items','cardToken'):
        if key not in body: errors.append({'field':key,'message':'This field is required.'})
    for key in ('userId','addressId'):
        if key in body and (not isinstance(body[key],int) or isinstance(body[key],bool) or body[key]<1): errors.append({'field':key,'message':'Must be a positive integer.'})
    if 'cardToken' in body and (not isinstance(body['cardToken'],str) or not body['cardToken'].strip()): errors.append({'field':'cardToken','message':'Must be a non-empty string.'})
    items=body.get('items')
    if isinstance(items,list) and not items: errors.append({'field':'items','message':'Cart must contain at least one item.'})
    elif not isinstance(items,list):
        if 'items' in body: errors.append({'field':'items','message':'Must be an array.'})
    else:
        for i,item in enumerate(items):
            if not isinstance(item,dict): errors.append({'field':f'items[{i}]','message':'Must be an object.'}); continue
            for key in ('itemId','quantity','unitPrice'):
                if key not in item: errors.append({'field':f'items[{i}].{key}','message':'This field is required.'})
            for key in ('itemId','quantity'):
                v=item.get(key)
                if v is not None and (not isinstance(v,int) or isinstance(v,bool) or v<1): errors.append({'field':f'items[{i}].{key}','message':'Must be an integer greater than or equal to 1.'})
            p=item.get('unitPrice')
            if p is not None and (not isinstance(p,str) or not re.fullmatch(r'\d+(\.\d{1,2})?',p) or Decimal(p)<=0): errors.append({'field':f'items[{i}].unitPrice','message':'Must be a positive decimal string with at most two decimal places.'})
    return errors
def create_app(store=None,payment_charge=charge):
    app=Flask(__name__); s=store or OrderStore(); app.config['RATE_LIMIT']=100; app.config['RATE_COUNTS']={}
    @app.before_request
    def auth_and_limit():
        if request.method=='OPTIONS': return None
        if not any(a.strip().split(';')[0] in ('*/*','application/json','application/xml') for a in request.headers.get('Accept','*/*').split(',')): return problem(406,'about:blank','Not Acceptable','Supported representations are application/json and application/xml.')
        if not request.headers.get('Authorization','').startswith('Bearer '): return problem(401,'about:blank','Unauthorized','Authorization: Bearer token is required.')
        ip=request.remote_addr or 'unknown'; counts=app.config['RATE_COUNTS']; n=counts.get(ip,0)
        if n>=app.config['RATE_LIMIT']: return problem(429,'about:blank','Too Many Requests','Request limit exceeded; retry later.',retry_after=60)
        counts[ip]=n+1
    @app.after_request
    def headers(r):
        r.headers['X-Content-Type-Options']='nosniff'; r.headers['Access-Control-Allow-Origin']='*'; r.headers['Access-Control-Allow-Methods']='GET, POST, PATCH, PUT, DELETE, OPTIONS'; r.headers['Access-Control-Allow-Headers']='Authorization, Content-Type, Idempotency-Key, If-None-Match, If-Match';
        if r.status_code!=304 and r.get_data() and not r.headers.get('Content-Type','').startswith(('application/json','application/problem+json','application/xml')): r.content_type='application/json; charset=utf-8'
        elif r.headers.get('Content-Type','').startswith('application/json'): r.content_type='application/json; charset=utf-8'
        return r
    @app.errorhandler(BadRequest)
    def malformed(_): return problem(400,'about:blank','Bad Request','Malformed JSON body.')
    @app.errorhandler(404)
    def route_missing(_): return problem(404,'https://campuseats.example/problems/order-not-found','Not Found','No endpoint or order exists at this path.')
    @app.errorhandler(405)
    def method_missing(_): return problem(405,'about:blank','Method Not Allowed','This HTTP method is not supported for the resource.')
    @app.route('/orders',methods=['OPTIONS'])
    @app.route('/orders/<oid>',methods=['OPTIONS'])
    def options(oid=None):
        r=Response(status=204); r.headers['Allow']='GET, POST, OPTIONS' if oid is None else 'GET, PATCH, PUT, DELETE, POST, OPTIONS'; return r
    @app.route('/orders',methods=['POST'])
    def create():
        key=request.headers.get('Idempotency-Key')
        if not key:return problem(400,'about:blank','Bad Request','Idempotency-Key header is required.')
        if not request.is_json:return problem(400,'about:blank','Bad Request','Content-Type must be application/json.')
        body=request.get_json(); errors=validate(body)
        if errors:
            empty=any(e['field']=='items' and 'at least one' in e['message'] for e in errors)
            return problem(422,'https://campuseats.example/problems/empty-cart' if empty else 'https://campuseats.example/problems/validation-error','Validation Failed','Request fields are invalid.',errors)
        old=s.find_by_idempotency_key(key)
        if old: r=jsonify(old.as_json()); r.status_code=201; r.headers['Location']='/orders/'+old.public_id; return r
        total=sum(int(Decimal(i['unitPrice'])*100)*i['quantity'] for i in body['items'])
        try: txn=payment_charge(s.next_public_id,total,body['cardToken'],key)
        except PaymentDeclined as e: log.warning('payment declined: %s',e); return problem(422,'https://campuseats.example/problems/payment-declined','Payment Declined','Payment could not be approved.')
        except PaymentUnavailable as e: log.error('payments unavailable: %s',e); return problem(503,'https://campuseats.example/problems/payment-unavailable','Payment Unavailable','Payment service is temporarily unavailable.',retry_after=30)
        except Exception: log.exception('unexpected payment failure'); return problem(503,'about:blank','Service Unavailable','Order could not be processed temporarily.',retry_after=30)
        o=s.create(user_id=body['userId'],address_id=body['addressId'],items=body['items'],total_minor_units=total,status='confirmed',idempotency_key=key,payment_transaction_id=txn)
        data=o.as_json(); r=xml_response(201,data) if 'application/xml' in request.headers.get('Accept','') and 'application/json' not in request.headers.get('Accept','') else jsonify(data); r.status_code=201;r.headers['Location']='/orders/'+o.public_id;return r
    @app.get('/orders')
    def listing():
        raw=request.args.get('userId','')
        if not raw.isdigit() or int(raw)<1:return problem(400,'about:blank','Bad Request','userId must be a positive integer.')
        data={'orders':[o.as_json() for o in s.list_for_user(int(raw))],'page':1,'pageSize':20,'total':len(s.list_for_user(int(raw)))}
        return xml_response(200,data) if request.headers.get('Accept','').startswith('application/xml') else jsonify(data)
    @app.route('/orders/<oid>',methods=['GET'])
    def get(oid):
        o=s.get(oid)
        if not o:return problem(404,'https://campuseats.example/problems/order-not-found','Order Not Found','No order exists with the requested id.')
        tag=etag(o)
        if request.headers.get('If-None-Match')==tag:r=Response(status=304);r.headers['ETag']=tag;return r
        r=xml_response(200,o.as_json()) if request.headers.get('Accept','').startswith('application/xml') else jsonify(o.as_json());r.headers['ETag']=tag;return r
    @app.route('/orders/<oid>',methods=['PATCH','PUT'])
    def update(oid):
        o=s.get(oid)
        if not o:return problem(404,'https://campuseats.example/problems/order-not-found','Order Not Found','No order exists with the requested id.')
        if not request.headers.get('If-Match'):return problem(428,'about:blank','Precondition Required','If-Match header is required.')
        if request.headers['If-Match']!=etag(o):return problem(412,'about:blank','Precondition Failed','ETag does not match current order.')
        b=request.get_json(); errors=[]
        if not isinstance(b,dict):errors=[{'field':'body','message':'Must be an object.'}]
        else:
            if 'addressId' not in b:errors.append({'field':'addressId','message':'Required.'})
            elif not isinstance(b['addressId'],int) or b['addressId']<1:errors.append({'field':'addressId','message':'Must be a positive integer.'})
            if not isinstance(b.get('items'),list) or not b['items']:errors.append({'field':'items','message':'Must be a non-empty array.'})
        if errors:return problem(422,'https://campuseats.example/problems/validation-error','Validation Failed','Request fields are invalid.',errors)
        o.address_id=b['addressId'];o.items=b['items'];o.total_minor_units=sum(int(Decimal(i['unitPrice'])*100)*i['quantity'] for i in b['items']);return jsonify(o.as_json())
    @app.delete('/orders/<oid>')
    def delete(oid):
        if not s.get(oid):return problem(404,'https://campuseats.example/problems/order-not-found','Order Not Found','No order exists with the requested id.')
        s.delete(oid);return Response(status=204)
    @app.post('/orders/<oid>/cancellation')
    def cancel(oid):
        o=s.get(oid)
        if not o:return problem(404,'https://campuseats.example/problems/order-not-found','Order Not Found','No order exists with the requested id.')
        if o.status=='cancelled':return problem(409,'https://campuseats.example/problems/illegal-transition','Illegal Transition','A cancelled order cannot be cancelled again.')
        o.status='cancelled';return jsonify(o.as_json())
    return app
if __name__=='__main__': create_app().run(port=5000)
