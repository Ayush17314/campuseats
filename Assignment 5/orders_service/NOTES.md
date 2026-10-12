# CampusEats — Assignment 5

## TeamID 03
| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

## CampusEats method map
| Action | Method + URL | Safe | Idempotent |
| --- | --- | --- | --- |
| List/filter/sort/page | `GET /orders?userId=7&status=confirmed&sort=orderId&page=1&pageSize=20` | Yes | Yes |
| Read one | `GET /orders/{id}` | Yes | Yes |
| Create/checkout | `POST /orders` | No | No* |
| Replace address/items | `PUT /orders/{id}` | No | Yes |
| Remove | `DELETE /orders/{id}` | No | Yes |
| Cancel | `POST /orders/{id}/cancellation` | No | No |
| Discover/preflight | `OPTIONS /orders/{id}` | Yes | Yes |

`POST /orders` becomes retry-safe with `Idempotency-Key`: the same key returns the original `201`, `Location`, and representation without charging twice. Cancellation is a non-CRUD sub-resource. A constrained client may use `POST /orders/{id}` plus `X-HTTP-Method-Override: PUT` or `DELETE`; normal clients use the real verb.

## Headers table
| Endpoint | Request headers | Response headers |
| --- | --- | --- |
| `POST /orders` | Authorization, Content-Type, Idempotency-Key, Accept | Location, rate-limit, CORS, security |
| `GET /orders` | Authorization, Accept | rate-limit, CORS, security |
| `GET /orders/{id}` | Authorization, Accept, optional If-None-Match | ETag, Cache-Control, rate-limit |
| `PUT /orders/{id}` | Authorization, Content-Type, required If-Match | ETag, Cache-Control: no-store |
| `DELETE /orders/{id}` | Authorization | 204, rate-limit/security/CORS |
| cancellation | Authorization, optional JSON Content-Type | Cache-Control: no-store |
| OPTIONS | Origin, Access-Control-Request-* | Allow, Access-Control-Allow-* |

Bodies use `Content-Type: application/json`; unsupported Accept gets `406`. Large JSON gets gzip if requested. Limits are per client (X-Forwarded-For/remote address), with `429` and `Retry-After: 60`. The framework supplies Date/Server; production is HTTPS and HSTS is set.

## Safe-retry plan
| Risky endpoint | Mechanism | Why |
| --- | --- | --- |
| POST create | Idempotency-Key | Stops duplicate orders/payments after a lost response. |
| GET one | If-None-Match | Returns bodyless 304 for unchanged data. |
| PUT replace | If-Match | 412 rejects stale editors and prevents lost updates. |
| Cancellation | Observe state / avoid blind retry | A second transition conflicts with 409. |

## Full HTTP/1.1 exchange
**Request**
```http
POST /orders HTTP/1.1
Host: 127.0.0.1:5000
Authorization: Bearer demo-token
Accept: application/json
Content-Type: application/json
Idempotency-Key: order-7-001

{"userId":7,"addressId":11,"cardToken":"tok_demo","items":[{"itemId":3,"quantity":2,"unitPrice":"125.50"}]}
```
**Response**
```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /orders/ORD-000001
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains

{"orderId":"ORD-000001","status":"confirmed","totalAmount":"251.00"}
```

## Answers
1. POST `/orders` → 201; `Location` identifies its new resource. GET `/orders/{id}` → 200; `ETag` permits validation. DELETE → 204; no response body is required.
2. GET/OPTIONS are safe and idempotent; PUT/DELETE are unsafe but idempotent. Create/cancel are neither; create is retry-safe through Idempotency-Key.
3. An ETag such as `"a1..."` with matching If-None-Match returns 304 and saves transfer. A stale If-Match returns 412 and prevents a lost update.
4. `POST /orders` with `{"userId":7}` gives 400 (invalid contract). A valid request whose payment is declined gives 422 (domain refusal).
5. The browser blocks CORS; `Access-Control-Allow-Origin` fixes it.
6. GET one uses `Cache-Control: private, max-age=60`; PUT/cancel uses `no-store` because state must not be reused.
7. POST search fits very large, structured, or sensitive criteria; it gives up normal GET caching and bookmarkable/shareable URLs.
8. Location on 201 names the created resource; on 3xx it names the redirect target.
