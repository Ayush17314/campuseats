# CampusEats Orders Service - Assignment 4

## TeamID 03

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

## A2 - SOAP-style starting operations

Before modelling resources, the Orders operations would have been:

- `placeOrder(studentId, deliveryAddressId, items, cardToken)`
- `getOrder(orderId)`
- `listOrdersForStudent(studentId)`
- `cancelOrder(orderId)`

These follow the Orders responsibility from Assignment 2: order placement and
status management, while Payments remains responsible for charges.

## A4 - Resource table

| Method | URL | What it does | Success | Failure codes |
| --- | --- | --- | --- | --- |
| POST | `/orders` | Creates a confirmed order after Payments approves it. | 201 + `Location` | 400, 422, 503 |
| GET | `/orders/{orderId}` | Returns one order. | 200 | 404 |
| GET | `/orders?userId={userId}` | Returns the orders belonging to one student. | 200 | 400 |
| POST | `/orders/{orderId}/cancellation` | Changes a confirmed order to cancelled. | 200 | 404, 409 |

The durable nouns are **orders** and the **cancellation** sub-resource. URL paths contain no operation verbs. `POST /orders` is safely retryable when the client supplies `Idempotency-Key`: the store retains that key with the created order and returns the original `201`, representation, and `Location` on a repeat.

## A5 - Hard choice

Cancellation was the least comfortable operation to map to a resource because the original design called it a state-changing verb. I modelled it as `POST /orders/{orderId}/cancellation`: a cancellation is a durable state transition attached to exactly one order, rather than a verb in the URL. I rejected `POST /cancelOrder` because it hides the order identity in a command-shaped endpoint. I also rejected `DELETE /orders/{orderId}` because the order must remain as a financial and operational record after cancellation.

## D3 - Dependency fallback

When Payments is unreachable after three attempts, Orders returns `503 Payment unavailable` and creates no order. This is a fail-closed choice: treating the order as confirmed without a charge would create an unpaid order, while treating it as failed could lead a client to retry and be charged twice after an ambiguous timeout. Each attempt uses a 0.5-second timeout, exponential backoff plus jitter, and the same `Idempotency-Key`; only transport errors and 5xx responses retry, never 4xx responses.

## Assignment 3 comparison

1. `Assignment3/partner.wsdl` has **108** lines; `openapi.yaml` has **231** lines, a difference of **123** lines. The difference is mostly XML namespace, `message`, `portType`, `binding`, and `service` ceremony in WSDL versus resource paths and reusable JSON schemas in OpenAPI. The WSDL declared the SOAP transport/binding (`soap:binding` and `soapAction`) and a WS-Security header message; OpenAPI does not need either for this HTTP JSON service.

2. Assignment 3 recorded this SOAP fault: `<faultcode>soap:Client</faultcode><faultstring>Card declined</faultstring>`; its detail contains `<tns:errorCode>card_declined</tns:errorCode>`. Here it becomes `422 Unprocessable Content` with: `{"type":"https://campuseats.example/problems/payment-declined","title":"Payment declined","status":422,"detail":"Payments declined the charge"}`. Returning this business failure inside `200 OK` would tell proxies, observability tools, caches, and retry/error middleware that the request succeeded; those layers cannot reliably distinguish success from failure without parsing application-specific XML.

3. **Publish** still exists when Orders publishes `openapi.yaml` in the repository (and could publish it through a developer portal). **Find** still exists as a developer or deployment-time lookup of that documented contract and the `PAYMENTS_BASE_URL` configuration. **Bind** still exists when the HTTP client calls that configured base URL. The live UDDI registry disappeared; source control, an API catalogue, and environment configuration now perform its jobs without runtime registry resolution.

4. `validate_order()` in `app.py` now enforces the request shape before any body fields are used. Without it, a request with an empty `items` list could reach total calculation and payment, creating an empty order or causing an unhelpful server error instead of the documented `400` problem response.

5. I would still choose SOAP for a bank or campus-card clearing integration. A WS-Security-capable SOAP stack can provide standardised message-level signing and encryption that survives intermediaries, plus a formally defined fault contract. REST over TLS is sufficient for this student-facing Orders API, but that particular cross-organisational payment guarantee is worth the SOAP complexity.
