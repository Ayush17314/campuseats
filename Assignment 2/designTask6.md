
---

# `task6-validation.md`

```markdown
# Task 6 — Service Validation

Each CampusEats service is checked against the five properties of a
web service:

1. Reachable over a network
2. Self-contained
3. Has a contract
4. Independent
5. Loosely coupled

## Validation Table

| Service | Reachable | Self-contained | Has Contract | Independent | Loosely Coupled |
|---|---|---|---|---|---|
| Accounts | ✓ | ✓ | ✓ | ✓ | ✓ |
| Catalogue | ✓ | ✓ | ✓ | ✓ | ✓ |
| Orders | ✓ | ✓ | ✓ | ✓ | ✓ |
| Payments | ✓ | ✓ | ✓ | ✓ | ✓ |
| Delivery | ✓ | ✓ | ✓ | ✓ | ✓ |
| Notifications | ✓ | ✓ | ✓ | ✓ | ✓ |

## Accounts Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can call its published operations over the network. |
| Self-contained | ✓ | It manages user profiles, addresses and login responsibilities. |
| Has Contract | ✓ | Operations such as `getAddress()` and `getProfile()` define its interface. |
| Independent | ✓ | Its internal implementation can change without changing callers. |
| Loosely Coupled | ✓ | Other services use its contracts instead of accessing its internal data. |

## Catalogue Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can call catalogue operations over the network. |
| Self-contained | ✓ | It manages restaurants, menus, prices and item availability. |
| Has Contract | ✓ | `listRestaurants()`, `getMenu()` and `checkItem()` define its contract. |
| Independent | ✓ | Its internal implementation can change without changing Orders. |
| Loosely Coupled | ✓ | Orders uses `checkItem()` instead of directly accessing catalogue data. |

## Orders Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Students and other services can access its published operations. |
| Self-contained | ✓ | It manages carts, orders and order status. |
| Has Contract | ✓ | `addToCart()`, `placeOrder()`, `getOrder()` and `cancelOrder()` define its contract. |
| Independent | ✓ | Its internal order implementation can change without exposing its data. |
| Loosely Coupled | ✓ | It communicates with other services through their published contracts. |

## Payments Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Orders can call payment operations over the network. |
| Self-contained | ✓ | It handles payment and refund responsibilities. |
| Has Contract | ✓ | `charge()` and `refund()` define its public contract. |
| Independent | ✓ | The payment provider can be changed internally without changing Orders. |
| Loosely Coupled | ✓ | Orders receives payment results through the payment contract. |

## Delivery Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Orders can call delivery operations over the network. |
| Self-contained | ✓ | It manages riders, assignments and delivery tracking. |
| Has Contract | ✓ | `assignRider()` and `getTracking()` define its public operations. |
| Independent | ✓ | Its rider assignment and tracking implementation can change internally. |
| Loosely Coupled | ✓ | Orders requests delivery through the published contract. |

## Notifications Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can request notifications over the network. |
| Self-contained | ✓ | It handles notification delivery. |
| Has Contract | ✓ | `send()` defines the operation available to other services. |
| Independent | ✓ | Its notification provider can change internally. |
| Loosely Coupled | ✓ | Other services call `send()` rather than accessing its internal data. |

## Overall Result

All six CampusEats services satisfy the five required service properties.

The design maintains independent data ownership and uses service contracts
for communication. No service directly accesses another service's internal
data.