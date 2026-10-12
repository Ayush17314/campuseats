"""Orders domain record and its deliberately smaller public representation."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Order:
    internal_id: int
    public_id: str
    user_id: int
    address_id: int
    items: list[dict[str, Any]]
    total_minor_units: int
    status: str
    idempotency_key: str
    payment_transaction_id: str

    def as_json(self) -> dict[str, Any]:
        """Do not disclose internal IDs, idempotency keys, payment IDs, or card tokens."""
        return {
            "orderId": self.public_id,
            "userId": self.user_id,
            "addressId": self.address_id,
            "items": self.items,
            "totalAmount": f"{self.total_minor_units / 100:.2f}",
            "status": self.status,
        }
