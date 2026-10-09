"""In-process data owned exclusively by the Orders service."""

from models import Order
from typing import Any


class OrderStore:
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._idempotency: dict[str, str] = {}
        self._next_id = 1

    @property
    def next_public_id(self) -> str:
        return f"ORD-{self._next_id:06d}"

    def find_by_idempotency_key(self, key: str) -> Order | None:
        order_id = self._idempotency.get(key)
        return self._orders.get(order_id) if order_id else None

    def create(self, **attributes: Any) -> Order:
        internal_id = self._next_id
        self._next_id += 1
        order = Order(internal_id=internal_id, public_id=f"ORD-{internal_id:06d}", **attributes)
        self._orders[order.public_id] = order
        self._idempotency[order.idempotency_key] = order.public_id
        return order

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def delete(self, order_id: str) -> None:
        order = self._orders.pop(order_id)
        self._idempotency.pop(order.idempotency_key, None)

    def list_for_user(self, user_id: int) -> list[Order]:
        return [order for order in self._orders.values() if order.user_id == user_id]
