# Assignment 2 — CampusEats Service Design

This assignment designs CampusEats as a set of loosely coupled services for campus food ordering, payment, delivery, and notifications.

## Design artefacts

| File | Description |
| --- | --- |
| `design.pdf` | Design-task submission in PDF form. |
| `designtask3.pdf` | Task 3 submission PDF. |
| `designTask4.md` | Contract and orchestration flow for the central `placeOrder` operation, including inputs, outputs, errors, and hidden implementation details. |
| `designTask6.md` | Validation of the Accounts, Catalogue, Orders, Payments, Delivery, and Notifications services against the required web-service properties. |
| `designTask6.pdf` | PDF version of the Task 6 submission. |

## Database design

| File | Description |
| --- | --- |
| `schema.sql` | Logical SQL schema for users, catalogue, carts, orders, payments, delivery, and notifications. It preserves service ownership by avoiding cross-service database foreign keys. |
| `schema.drawio` | Editable Draw.io database schema diagram. |
| `Schema.png` | Exported image of the database schema. |

## Service architecture

| File | Description |
| --- | --- |
| `services-3.drawio` | Editable Draw.io diagram of the CampusEats service architecture. |
| `services.drawio-3.png` | Exported image of the service architecture diagram. |

## Core services

| Service | Responsibility |
| --- | --- |
| Accounts | Student profiles, authentication, and delivery addresses. |
| Catalogue | Restaurants, menus, prices, and item availability. |
| Orders | Carts, order placement, and order status. |
| Payments | Charges and refunds. |
| Delivery | Rider assignment and delivery tracking. |
| Notifications | Order-related messages to students. |

`Orders.placeOrder` coordinates the order flow by validating the address and items, charging payment, creating the order, assigning a rider, and sending a notification through service contracts.
