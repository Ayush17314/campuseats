# CampusEats — Assignment 5 & Assignment 6 Notes

## TeamID 03

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

---

## 1. Status map (Part A1 & A2)

Every failure is routed through [`problem()`](errors.py) and returns `Content-Type: application/problem+json; charset=utf-8` with `type`, `title`, `status`, and `detail` (plus `errors[]` for field validation failures). No endpoint ever returns `200 OK` with `{"ok": false}` for a failure.

| Endpoint | Success Status | Failure Statuses & One-Line Reason |
| --- | --- | --- |
| `POST /orders` | `201 Created` (`Location: /orders/{id}`) | `400` malformed JSON, missing `Idempotency-Key`, or wrong `Content-Type`; `401` missing/empty Bearer token; `406` unsupported `Accept`; `422` empty cart, invalid fields (`errors[]`), unavailable item, or declined payment; `429` rate limit exceeded (`Retry-After: 60`); `503` payment service unavailable after retries (`Retry-After: 30`). |
| `GET /orders?userId=...` | `200 OK` | `400` missing or invalid `userId`, `sort`, `page`, or `pageSize` query parameters; `401` missing/empty Bearer token; `406` unsupported `Accept`; `429` rate limit exceeded (`Retry-After: 60`). |
| `GET /orders/{orderId}` | `200 OK` (or `304 Not Modified` when `If-None-Match` matches `ETag`) | `401` missing/empty Bearer token; `404` order ID does not exist; `406` unsupported `Accept`; `429` rate limit exceeded (`Retry-After: 60`). |
| `PATCH /orders/{orderId}` & `PUT /orders/{orderId}` | `200 OK` (with updated `ETag`) | `400` malformed JSON or non-JSON `Content-Type`; `401` missing/empty Bearer token; `404` order ID does not exist; `406` unsupported `Accept`; `409` order is already cancelled; `412` stale `If-Match` ETag; `422` invalid replacement fields or unavailable item; `428` missing `If-Match` header; `429` rate limit exceeded (`Retry-After: 60`). |
| `DELETE /orders/{orderId}` | `204 No Content` | `401` missing/empty Bearer token; `404` order ID does not exist; `406` unsupported `Accept`; `429` rate limit exceeded (`Retry-After: 60`). |
| `POST /orders/{orderId}/cancellation` | `200 OK` | `400` non-JSON body when a request body is supplied; `401` missing/empty Bearer token; `404` order ID does not exist; `406` unsupported `Accept`; `409` order is already cancelled (`illegal-transition`); `429` rate limit exceeded (`Retry-After: 60`). |
| `OPTIONS /orders` & `OPTIONS /orders/{orderId}` | `204 No Content` (with `Allow` header) | `405` when an unsupported HTTP method is sent to a known resource path. |

---

## 2. Stable Problem Details type catalogue (Part B2)

| Problem `type` URI | HTTP Status | Trigger Condition |
| --- | --- | --- |
| `https://campuseats.example/problems/empty-cart` | `422` | `items` in the order payload is an empty array (`[]`). |
| `https://campuseats.example/problems/validation-error` | `422` | One or more request fields fail schema or domain validation (missing fields, `userId < 1`, `addressId < 1`, `quantity < 1`, malformed `unitPrice`, or unexpected fields). |
| `https://campuseats.example/problems/item-unavailable` | `422` | A requested catalogue `itemId` (e.g., `999`) is unavailable for ordering. |
| `https://campuseats.example/problems/payment-declined` | `422` | The Payments service reached the gateway and explicitly declined the charge (`HTTP 402`). |
| `https://campuseats.example/problems/payment-unavailable` | `503` | The Payments service timed out, returned `5xx`, or failed after 3 bounded retry attempts (includes `Retry-After: 30`). |
| `https://campuseats.example/problems/order-not-found` | `404` | The requested `orderId` (or endpoint path) does not exist in `OrderStore`. |
| `https://campuseats.example/problems/illegal-transition` | `409` | The caller attempts to cancel an order that is already `cancelled`, or attempts to `PATCH`/`PUT` a `cancelled` order. |
| `about:blank` | `400, 401, 405, 406, 412, 428, 429, 500` | Standard HTTP protocol errors where the HTTP status code itself identifies the condition (malformed JSON, missing `Authorization: Bearer`, method not allowed, unsupported `Accept`, stale/missing `If-Match`, rate limiting with `Retry-After: 60`, or unexpected internal error). |

---

## 3. Problem Details body and field meanings (Part B1)

Example returned for `GET /orders/ORD-999999`:

```json
{
  "type": "https://campuseats.example/problems/order-not-found",
  "title": "Order Not Found",
  "status": 404,
  "detail": "No order exists with the requested id."
}
```

- **`type`**: Stable URI identifier classifying the problem category from the service's error catalogue.
- **`title`**: Short, human-readable summary of the problem type that stays constant across occurrences of this `type`.
- **`status`**: Integer HTTP status code (`404`) matching the actual HTTP response status line.
- **`detail`**: Human-readable explanation specific to this occurrence of the problem.
- **`errors`** *(present on `422` validation failures)*: Array of `{"field": "<path>", "message": "<reason>"}` objects pinpointing every invalid field in one response.

---

## 4. Field-level `422` reporting multiple bad fields at once (Part B3 & C2)

[`validate()`](app.py) inspects the entire request payload before any business logic or payment call runs, collecting **all** invalid fields into `errors[]` rather than stopping at the first failure.

Submitting `userId: 0`, `addressId: 0`, and `items[0].quantity: 0` in a single `POST /orders` request returns:

```json
{
  "type": "https://campuseats.example/problems/validation-error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Request fields are invalid.",
  "errors": [
    {
      "field": "userId",
      "message": "Must be a positive integer."
    },
    {
      "field": "addressId",
      "message": "Must be a positive integer."
    },
    {
      "field": "items[0].quantity",
      "message": "Must be an integer greater than or equal to 1."
    }
  ]
}
```

---

## 5. Retry safety and status codes (Part A4)

- **`GET /orders` & `GET /orders/{orderId}`**: Safe and idempotent; always safe to retry. Sending `If-None-Match` with the current `ETag` returns `304 Not Modified` without transferring the body again.
- **`POST /orders` (with `Idempotency-Key`)**: Safe to retry **with the exact same `Idempotency-Key`** after a network timeout or `503 Service Unavailable`. If the original attempt succeeded before the connection dropped, re-sending the key returns the original `201 Created` response and `Location` without charging the card a second time.
- **`PUT /orders/{orderId}` & `PATCH /orders/{orderId}` (with `If-Match`)**: Idempotent and safe to retry against transient failures because `If-Match` guards against overwriting concurrent modifications (`412 Precondition Failed` requires fetching the fresh `ETag` before retrying).
- **`DELETE /orders/{orderId}`**: Idempotent in intended effect, though a repeat call after a `204 No Content` returns `404 Not Found`.
- **`POST /orders/{orderId}/cancellation`**: State transition; a repeat call after `200 OK` returns `409 Conflict` (`illegal-transition`), so callers should inspect `GET /orders/{orderId}` rather than blindly retrying.
- **Status codes signaling retryability**:
  - **`429 Too Many Requests`** (includes `Retry-After: 60`) and **`503 Service Unavailable`** (includes `Retry-After: 30`) explicitly tell the client that the failure is transient and when it may retry.
  - **Never retry unchanged `4xx` responses (`400`, `401`, `404`, `405`, `406`, `409`, `412`, `422`, `428`)**: The client must fix the request payload, credentials, or `If-Match` precondition first.

---

## 6. Mapping internal errors to clean client errors & hiding internals (Part B4)

In [`app.py`](app.py) (`create()` and `@app.errorhandler(Exception)`) and [`payment_client.py`](payment_client.py):
1. **Payment boundary mapping (`app.py` lines 202–212 & `payment_client.py` lines 36–56)**:
   - Low-level socket timeouts (`TimeoutError`), DNS/connection refusals (`urllib.error.URLError`), upstream `5xx` responses, missing `PAYMENTS_BASE_URL` configuration, and unexpected runtime exceptions during payment processing are caught in `try / except`.
   - The full exception details and stack trace are logged server-side via `log.error(...)` and `log.exception(...)`, while the client receives a clean `503 Service Unavailable` Problem Details response (`type: "https://campuseats.example/problems/payment-unavailable"`, `detail: "Payment service is temporarily unavailable."`, `Retry-After: 30`).
2. **Global unhandled exception fallback (`app.py` lines 169–172)**:
   - `@app.errorhandler(Exception)` logs the full Python traceback server-side and returns a clean `500 Internal Server Error` Problem Details payload (`detail: "An unexpected internal error occurred."`).
3. **What is hidden from the caller**:
   - Python stack traces, file paths, and line numbers
   - Internal upstream URLs (`PAYMENTS_BASE_URL`), socket/DNS error messages, and connection strings
   - Internal database/store sequence IDs (`internal_id`), `idempotency_key`, `payment_transaction_id`, and `cardToken` (stripped by [`Order.as_json()`](models.py)).

---

## 7. Content negotiation: same order as JSON and XML (Part C3 & C4)

### JSON Representation (`Accept: application/json`)
- **Request header**: `Accept: application/json`
- **Response header**: `Content-Type: application/json; charset=utf-8`
- **Body**:
```json
{
  "addressId": 11,
  "items": [
    {
      "itemId": 3,
      "quantity": 2,
      "unitPrice": "125.50"
    }
  ],
  "orderId": "ORD-000001",
  "status": "confirmed",
  "totalAmount": "251.00",
  "userId": 7
}
```

### XML Representation (`Accept: application/xml`)
- **Request header**: `Accept: application/xml`
- **Response header**: `Content-Type: application/xml; charset=utf-8`
- **Body**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<order><orderId>ORD-000001</orderId><userId>7</userId><addressId>11</addressId><items><item><itemId>3</itemId><quantity>2</quantity><unitPrice>125.50</unitPrice></item></items><totalAmount>251.00</totalAmount><status>confirmed</status></order>
```

---

## 8. Assignment 5 Protocol Summary (Preserved with Zero Regressions)

| Action | Method + URL | Safe | Idempotent | Key Headers |
| --- | --- | --- | --- | --- |
| List/filter/sort/page | `GET /orders?userId=7&status=confirmed&sort=orderId&page=1&pageSize=20` | Yes | Yes | `Authorization`, `Accept` -> `X-RateLimit-*`, `Content-Type` |
| Read one | `GET /orders/{id}` | Yes | Yes | `Authorization`, `Accept`, `If-None-Match` -> `ETag`, `Cache-Control: private, max-age=60` |
| Create/checkout | `POST /orders` | No | Retry-safe via `Idempotency-Key` | `Authorization`, `Idempotency-Key`, `Content-Type` -> `201`, `Location` |
| Update/replace | `PATCH /orders/{id}` or `PUT /orders/{id}` | No | Yes | `Authorization`, `If-Match`, `Content-Type` -> `ETag`, `Cache-Control: no-store` |
| Remove | `DELETE /orders/{id}` | No | Yes | `Authorization` -> `204 No Content` |
| Cancel | `POST /orders/{id}/cancellation` | No | No | `Authorization` -> `200 OK`, `Cache-Control: no-store` |
| Discover/preflight | `OPTIONS /orders/{id}` | Yes | Yes | `Allow`, `Access-Control-Allow-*` |
