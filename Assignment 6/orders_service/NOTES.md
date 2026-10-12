# CampusEats Assignment 6 — TeamID 03

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

## 1. Status map

Failures use Problem Details with type, title, status, and detail. Validation errors also include errors[].

| Endpoint | Success | Failure statuses and reason |
| --- | --- | --- |
| POST /orders | 201 Created with Location: /orders/{id} | 400 malformed JSON, missing idempotency key, or wrong request content type; 401 missing bearer authorization; 406 unsupported Accept; 422 invalid fields, empty cart, or declined payment; 429 rate limit; 503 payment service unavailable. |
| GET /orders?userId=... | 200 OK | 400 missing or invalid userId; 401 unauthorized; 406 unsupported Accept; 429 rate limit. |
| GET /orders/{orderId} | 200 OK; 304 Not Modified when If-None-Match matches | 404 unknown order; 401 unauthorized; 406 unsupported Accept; 429 rate limit. |
| PATCH /orders/{orderId} (PUT is also accepted) | 200 OK | 400 malformed JSON; 401 unauthorized; 404 unknown order; 406 unsupported Accept; 412 stale If-Match; 422 invalid replacement fields; 428 missing If-Match; 429 rate limit. |
| DELETE /orders/{orderId} | 204 No Content | 401 unauthorized; 404 unknown order; 406 unsupported Accept; 429 rate limit. |
| POST /orders/{orderId}/cancellation | 200 OK | 401 unauthorized; 404 unknown order; 406 unsupported Accept; 409 order already cancelled; 429 rate limit. |

Unsupported paths and methods return 404 and 405 respectively. Rate-limit responses include Retry-After: 60; transient payment 503 includes Retry-After: 30.

## 2. Stable Problem Details type catalogue

- https://campuseats.example/problems/empty-cart — items is an empty array.
- https://campuseats.example/problems/validation-error — one or more submitted fields fail validation.
- https://campuseats.example/problems/item-unavailable — reserved for an inventory check that rejects an order item; the current service has no inventory lookup to trigger this condition.
- https://campuseats.example/problems/payment-declined — Payments explicitly declines the charge.
- https://campuseats.example/problems/payment-unavailable — Payments cannot be reached or does not complete the charge after transient retries.
- https://campuseats.example/problems/order-not-found — requested order ID does not exist.
- https://campuseats.example/problems/illegal-transition — cancellation is requested for an order already cancelled.
- about:blank — general HTTP conditions such as authentication failure, unsupported representation, rate limiting, or failed request preconditions.

## 3. Problem Details body and field meanings

Example returned for an unknown order ID:

    {
      "type": "https://campuseats.example/problems/order-not-found",
      "title": "Order Not Found",
      "status": 404,
      "detail": "No order exists with the requested id."
    }

The type is the stable problem identifier; title is a short summary; status repeats the HTTP status; detail explains this occurrence. Validation responses add errors, an array of field and message entries.


## 4. One response reporting multiple invalid fields

The transcript submits userId=0, addressId=0, and items[0].quantity=0. It receives one 422 response whose errors array identifies all three fields and explains that each must be a positive integer. Validation rejects the request before payment is attempted.