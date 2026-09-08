# Curl transcript

The Payments-compatible service was running at `http://localhost:5001` and
Orders at `http://localhost:5000`. The following commands were run in
PowerShell. `--data-binary "@-"` reads JSON from standard input, preserving
quotation marks when calling `curl.exe` from PowerShell.

Restart both services before a fresh run because Orders uses in-memory
storage. The commands capture the order ID from the first response, so the
cancellation commands work regardless of whether the new ID is `ORD-000001`
or a later ID. The outputs below were captured from one run, which created
`ORD-000002`.

## Create an order — 201 and Location

```powershell
$body = '{"userId":7,"addressId":11,"cardToken":"tok_demo","items":[{"itemId":3,"quantity":2,"unitPrice":"125.50"}]}'
$created = $body | curl.exe -i -sS -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: a4-transcript-002" --data-binary "@-"
$createdText = $created -join "`n"
$createdText
$orderId = [regex]::Match($createdText, 'Location: /orders/(ORD-[0-9]{6})').Groups[1].Value
```

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /orders/ORD-000002

{
  "addressId": 11,
  "items": [{"itemId": 3, "quantity": 2, "unitPrice": "125.50"}],
  "orderId": "ORD-000002",
  "status": "confirmed",
  "totalAmount": "251.00",
  "userId": 7
}
```

##  idempotency key — original 201 result

```powershell
$body | curl.exe -i -sS -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: a4-transcript-002" --data-binary "@-"
```

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /orders/ORD-000002

{
  "addressId": 11,
  "items": [{"itemId": 3, "quantity": 2, "unitPrice": "125.50"}],
  "orderId": "ORD-000002",
  "status": "confirmed",
  "totalAmount": "251.00",
  "userId": 7
}
```

## Malformed request body — 400

```powershell
'{"userId":7}' | curl.exe -i -sS -X POST http://localhost:5000/orders -H "Content-Type: application/json" -H "Idempotency-Key: malformed-002" --data-binary "@-"
```

```http
HTTP/1.1 400 BAD REQUEST
Content-Type: application/problem+json

{
  "detail": "Missing required field(s): addressId, cardToken, items.",
  "status": 400,
  "title": "Invalid request",
  "type": "https://campuseats.example/problems/invalid-request"
}
```

## Missing order — 404

```powershell
curl.exe -i -sS http://localhost:5000/orders/ORD-999999
```

```http
HTTP/1.1 404 NOT FOUND
Content-Type: application/problem+json

{
  "detail": "No order exists with id ORD-999999.",
  "status": 404,
  "title": "Order not found",
  "type": "https://campuseats.example/problems/order-not-found"
}
```

## Cancellation, then state conflict — 200 and 409

```powershell
curl.exe -i -sS -X POST "http://localhost:5000/orders/$orderId/cancellation"
curl.exe -i -sS -X POST "http://localhost:5000/orders/$orderId/cancellation"
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "addressId": 11,
  "items": [{"itemId": 3, "quantity": 2, "unitPrice": "125.50"}],
  "orderId": "ORD-000002",
  "status": "cancelled",
  "totalAmount": "251.00",
  "userId": 7
}

HTTP/1.1 409 CONFLICT
Content-Type: application/problem+json

{
  "detail": "A cancelled order cannot be cancelled again.",
  "status": 409,
  "title": "Order state conflict",
  "type": "https://campuseats.example/problems/order-state-conflict"
}
```
