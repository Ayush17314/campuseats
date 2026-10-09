"""Resilient HTTP boundary client for the independently owned Payments service."""

import json
import os
import random
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PaymentUnavailable(Exception):
    """Payment cannot be safely confirmed."""


class PaymentDeclined(Exception):
    """Payment was reached and declined the charge."""


def charge(order_id: str, amount_minor_units: int, card_token: str, idempotency_key: str) -> str:
    """Retry only network/timeout/5xx failures and forward the same idempotency key."""
    base_url = os.environ.get("PAYMENTS_BASE_URL")
    if not base_url:
        raise PaymentUnavailable("PAYMENTS_BASE_URL is not configured.")
    base_url = base_url.rstrip("/")
    request = Request(
        f"{base_url}/charges",
        data=json.dumps({
            "orderId": order_id,
            "amountMinorUnits": amount_minor_units,
            "cardToken": card_token,
        }).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Idempotency-Key": idempotency_key},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=0.5) as response:
                body = json.load(response)
                transaction_id = body.get("transactionId")
                if not transaction_id:
                    raise PaymentUnavailable("Payments returned no transaction id.")
                return str(transaction_id)
        except HTTPError as error:
            if error.code == 402:
                raise PaymentDeclined("Payments declined the charge.") from error
            if 400 <= error.code < 500:
                raise PaymentUnavailable("Payments rejected this request.") from error
            last_error = error  # 5xx is safe to retry.
        except PaymentUnavailable:
            raise
        except (URLError, TimeoutError) as error:
            last_error = error
        if attempt < 2:
            time.sleep((0.05 * (2**attempt)) + random.uniform(0, 0.025))
    raise PaymentUnavailable("Payments could not be reached after three attempts.") from last_error
