# Task 4 — Central Operation: placeOrder

## Purpose

`placeOrder` allows a student to submit selected food items for delivery.

The Orders Service coordinates the required service calls while hiding
its internal implementation from the caller.

## Inputs

| Field | Description |
|---|---|
| `studentId` | Identifies the student placing the order |
| `items` | List of requested food items and quantities |
| `deliveryAddressId` | Address where the order should be delivered |
| `paymentMethodId` | Payment method selected by the student |

### Item Input

| Field | Description |
|---|---|
| `itemId` | Food item being ordered |
| `quantity` | Number of units requested |

## Output

| Field | Description |
|---|---|
| `orderId` | Reference for the placed order |
| `status` | Current order status |
| `total` | Final order amount |
| `estimatedMinutes` | Estimated delivery time |

## Error Cases

| Error | Meaning |
|---|---|
| `EMPTY_CART` | No food items were provided |
| `INVALID_ADDRESS` | The delivery address is invalid or unavailable |
| `ITEM_NOT_FOUND` | A requested food item does not exist |
| `ITEM_UNAVAILABLE` | A requested food item is currently unavailable |
| `INVALID_QUANTITY` | The requested quantity is invalid |
| `PAYMENT_DECLINED` | The payment was rejected |
| `PAYMENT_FAILED` | Payment processing failed |
| `NO_RIDER_AVAILABLE` | A rider cannot currently be assigned |

## Internal Processing

1. Validate the delivery address through the Accounts Service.
2. Call `Catalogue.checkItem()` for each requested item.
3. Obtain item availability and current prices.
4. Calculate the order total.
5. Call `Payments.charge()` to process payment.
6. Create and confirm the order after successful payment.
7. Call `Delivery.assignRider()` to arrange delivery.
8. Call `Notifications.send()` to notify the student.
9. Return the order result to the student.

## Internal Details Hidden from Callers

The caller does not need to know:

- How the order is stored internally.
- How order references are generated.
- How carts are implemented.
- How food prices are stored.
- Which payment gateway or provider is used.
- How payment transactions are implemented.
- How riders are selected.
- How delivery tracking is implemented.
- How notifications are stored or delivered.
- Which database technology is used.
- Any SQL or internal database structure.

## Contract

```text
placeOrder(input) → output or error