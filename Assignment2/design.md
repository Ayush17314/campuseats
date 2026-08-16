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