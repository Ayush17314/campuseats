# CampusEats — Service Contracts

## 1. Accounts Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| getAddress | studentId, addressId | Delivery address | Address not found |
| getProfile | studentId | User profile | User not found |

## 2. Catalogue Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| listRestaurants | Area or filter | List of restaurants | No restaurants found |
| getMenu | restaurantId | Menu items with prices | Restaurant not found |
| checkItem | itemId | Availability and current price | Item not found |

## 3. Orders Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| addToCart | studentId, itemId, quantity | Updated cart | Item unavailable, invalid quantity |
| placeOrder | studentId, items, deliveryAddressId, paymentMethodId | Order reference, status, total, estimated time | Empty cart, invalid address, item unavailable, payment declined |
| getOrder | orderId | Order details and status | Order not found |
| cancelOrder | orderId | Cancellation status | Order not found, too late to cancel |

## 4. Payments Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| charge | Order reference, amount, payment method | Payment receipt and status | Payment declined, invalid payment method |
| refund | Payment reference, amount | Refund status | Payment not found, refund rejected |

## 5. Delivery Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| assignRider | Order reference, delivery location | Rider assignment and estimated time | No rider available, invalid order |
| getTracking | Order reference | Delivery status, location, estimated time | Delivery not found |

## 6. Notifications Service

| Operation | Input | Output | Errors |
|---|---|---|---|
| send | Recipient, message, notification type | Notification status | Invalid recipient, delivery failed |


# Central Operation — placeOrder

## Purpose

`placeOrder` allows a student to submit selected food items for delivery.
The Orders Service coordinates validation, catalogue checking, payment,
rider assignment, and notification.

## Input

| Field | Description |
|---|---|
| `studentId` | Identifies the student placing the order |
| `items` | List of food items and requested quantities |
| `deliveryAddressId` | Address where the order should be delivered |
| `paymentMethodId` | Payment method selected by the student |

### Item Input

Each item contains:

| Field | Description |
|---|---|
| `itemId` | Food item being ordered |
| `quantity` | Number of units requested |

Example:

```text# Central Operation — placeOrder

## Purpose

`placeOrder` allows a student to submit selected food items for delivery.
The Orders Service coordinates validation, catalogue checking, payment,
rider assignment, and notification.

## Input

| Field | Description |
|---|---|
| `studentId` | Identifies the student placing the order |
| `items` | List of food items and requested quantities |
| `deliveryAddressId` | Address where the order should be delivered |
| `paymentMethodId` | Payment method selected by the student |

### Item Input

Each item contains:

| Field | Description |
|---|---|
| `itemId` | Food item being ordered |
| `quantity` | Number of units requested |

Example:

```text
placeOrder(
    studentId,
    items: [
        { itemId, quantity },
        { itemId, quantity }
    ],
    deliveryAddressId,
    paymentMethodId
)
placeOrder(
    studentId,
    items: [
        { itemId, quantity },
        { itemId, quantity }
    ],
    deliveryAddressId,
    paymentMethodId
)

# Service Validation — Five Properties

Each CampusEats service is evaluated against the five properties of a
good web service.

| Service | Reachable | Self-contained | Has Contract | Independent | Loosely Coupled |
|---|---|---|---|---|---|
| Accounts | ✓ | ✓ | ✓ | ✓ | ✓ |
| Catalogue | ✓ | ✓ | ✓ | ✓ | ✓ |
| Orders | ✓ | ✓ | ✓ | ✓ | ✓ |
| Payments | ✓ | ✓ | ✓ | ✓ | ✓ |
| Delivery | ✓ | ✓ | ✓ | ✓ | ✓ |
| Notifications | ✓ | ✓ | ✓ | ✓ | ✓ |

## Validation Details

### Accounts Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can call its published operations over the network. |
| Self-contained | ✓ | It manages user profiles and delivery addresses as its own capability. |
| Has Contract | ✓ | Operations such as `getAddress()` and `getProfile()` define its interface. |
| Independent | ✓ | Its internal implementation can change without changing callers. |
| Loosely Coupled | ✓ | Other services request account information through contracts rather than accessing its data directly. |

### Catalogue Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can call catalogue operations over the network. |
| Self-contained | ✓ | It manages restaurants, menus, prices, and item availability. |
| Has Contract | ✓ | `listRestaurants()`, `getMenu()`, and `checkItem()` define its contract. |
| Independent | ✓ | Catalogue implementation can change without changing Orders. |
| Loosely Coupled | ✓ | Orders uses `checkItem()` instead of accessing catalogue data directly. |

### Orders Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Students and other services can access its published operations. |
| Self-contained | ✓ | It manages carts, orders, and order status. |
| Has Contract | ✓ | `addToCart()`, `placeOrder()`, `getOrder()`, and `cancelOrder()` define its contract. |
| Independent | ✓ | Its internal order implementation can change without exposing its data to other services. |
| Loosely Coupled | ✓ | It communicates with Accounts, Catalogue, Payments, Delivery, and Notifications through contracts. |

### Payments Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Orders can call payment operations over the network. |
| Self-contained | ✓ | It performs payment and refund responsibilities itself. |
| Has Contract | ✓ | `charge()` and `refund()` define its public contract. |
| Independent | ✓ | The payment provider can be changed internally without changing Orders. |
| Loosely Coupled | ✓ | Orders receives payment results through `charge()` instead of accessing payment data. |

### Delivery Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Orders can call delivery operations over the network. |
| Self-contained | ✓ | It manages riders, assignments, and delivery tracking. |
| Has Contract | ✓ | `assignRider()` and `getTracking()` define its public operations. |
| Independent | ✓ | Rider assignment and tracking implementation can change internally. |
| Loosely Coupled | ✓ | Orders requests rider assignment through a contract instead of accessing rider data. |

### Notifications Service

| Property | Result | Reason |
|---|---|---|
| Reachable | ✓ | Other services can request notifications over the network. |
| Self-contained | ✓ | It performs the notification delivery responsibility. |
| Has Contract | ✓ | `send()` defines the operation available to other services. |
| Independent | ✓ | Its notification provider or implementation can change without changing callers. |
| Loosely Coupled | ✓ | Services call `send()` rather than accessing the notification log directly. |

## Overall Result

All six CampusEats services satisfy the five required service properties.

The design maintains independent data ownership and uses service contracts
for communication. No service directly accesses another service's internal
data.