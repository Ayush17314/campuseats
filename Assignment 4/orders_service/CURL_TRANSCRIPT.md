# Curl transcript commands

Start the service with `python app.py`, then run these commands from this directory. The output is intentionally captured with `-i` so it includes the status line and headers required for submission.

```powershell
$body = '{"userId":7,"addressId":11,"cardToken":"tok_demo","items":[{"itemId":3,"quantity":2,"unitPrice":"125.50"}]}'
curl.exe -i -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: a4-demo-001" --data $body
# Expected: HTTP/1.1 201 CREATED and Location: /orders/ORD-000001

curl.exe -i -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: a4-demo-001" --data $body
# Expected: the same HTTP/1.1 201 CREATED, Location, and JSON representation.

curl.exe -i -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: malformed-001" --data '{"userId":7}'
# Expected: HTTP/1.1 400 BAD REQUEST and an application/problem+json body.

curl.exe -i http://localhost:5000/orders/ORD-999999
# Expected: HTTP/1.1 404 NOT FOUND and an application/problem+json body.

curl.exe -i -X POST http://localhost:5000/orders/ORD-000001/cancellation
curl.exe -i -X POST http://localhost:5000/orders/ORD-000001/cancellation
# Expected: the second cancellation is HTTP/1.1 409 CONFLICT and an application/problem+json body.
```

> Before capturing the successful-create transcript, run the Tutorial 4 Payments service and set `PAYMENTS_BASE_URL` to its HTTP base URL. The supplied test suite injects an approved payment response, so tests do not need a live payment server.
