# CampusEats — Project Brief

## What it does

CampusEats is a food-ordering app for a college campus. A student opens the app,
browses restaurants and menus, adds items to a cart, and places an order. They pay
online, a delivery rider is assigned and brings the food over, and the student can
track it in real time. At each step order placed, paid, on the way, delivered,
the student gets a notification.

## Who uses it

- **Students**  the main users. They log in, manage their profile and addresses,
  browse food, order, pay, and track delivery.
- **Restaurants** supply the menus and prices students browse from.
- **Riders** get assigned to orders and deliver them.

## The nouns (the things / services)

1. **Accounts**  owns users, addresses, login
2. **Catalogue**  owns restaurants, menus, prices
3. **Orders** owns carts, orders, order status
4. **Payments**  owns transactions, refunds
5. **Delivery**  owns riders, rider assignments
6. **Notifications**  owns the message log

## The verbs (the actions / tasks / contracts)

- **Accounts:** register, login, updateProfile, addAddress
- **Catalogue:** listRestaurants, getMenu, checkItem
- **Orders:** addToCart, placeOrder, getOrder, cancelOrder
- **Payments:** charge, refund
- **Delivery:** assignRider, trackDelivery
- **Notifications:** send

A full order flow ties these together: a student calls `Orders.placeOrder`, which
calls `Catalogue.checkItem` (still available? what's the price?), `Payments.charge`
(take the money), `Delivery.assignRider` (get it moving), and `Notifications.send`
(tell the student).