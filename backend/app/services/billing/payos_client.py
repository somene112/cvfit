"""Backend-only payOS payment-link client.

This module implements checkout-link creation only. Webhook verification and
payment confirmation deliberately live outside this PR.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from typing import Any

import httpx

from app.core.config import settings


PAYOS_CREATE_PAYMENT_URL = "https://api-merchant.payos.vn/v2/payment-requests"
PAYOS_TIMEOUT_SECONDS = 10.0


class BillingProviderError(RuntimeError):
    """Safe base error for provider failures."""


class BillingProviderConfigError(BillingProviderError):
    """Raised when required backend-only provider configuration is absent."""


class BillingProviderRequestError(BillingProviderError):
    """Raised when payOS rejects or cannot complete link creation."""


@dataclass(frozen=True)
class PaymentLinkResult:
    checkout_url: str
    payment_link_id: str | None
    sanitized_payload: dict[str, Any]


class PayOSClient:
    """Small provider boundary for the payOS create-payment-link API."""

    def __init__(
        self,
        *,
        client_id: str,
        api_key: str,
        checksum_key: str,
        return_url: str,
        cancel_url: str,
        timeout_seconds: float = PAYOS_TIMEOUT_SECONDS,
        http_client: httpx.Client | None = None,
    ) -> None:
        required = {
            "PAYOS_CLIENT_ID": client_id,
            "PAYOS_API_KEY": api_key,
            "PAYOS_CHECKSUM_KEY": checksum_key,
            "PAYMENT_RETURN_URL": return_url,
            "PAYMENT_CANCEL_URL": cancel_url,
        }
        if any(not value.strip() for value in required.values()):
            raise BillingProviderConfigError("billing provider is not configured")

        self._client_id = client_id
        self._api_key = api_key
        self._checksum_key = checksum_key
        self.return_url = return_url
        self.cancel_url = cancel_url
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client

    @classmethod
    def from_settings(cls) -> "PayOSClient":
        return cls(
            client_id=settings.PAYOS_CLIENT_ID,
            api_key=settings.PAYOS_API_KEY,
            checksum_key=settings.PAYOS_CHECKSUM_KEY,
            return_url=settings.PAYMENT_RETURN_URL,
            cancel_url=settings.PAYMENT_CANCEL_URL,
        )

    def create_payment_link(
        self,
        *,
        order_code: int,
        amount_vnd: int,
        description: str,
    ) -> PaymentLinkResult:
        signature_data = (
            f"amount={amount_vnd}&cancelUrl={self.cancel_url}"
            f"&description={description}&orderCode={order_code}"
            f"&returnUrl={self.return_url}"
        )
        signature = hmac.new(
            self._checksum_key.encode("utf-8"),
            signature_data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        payload = {
            "orderCode": order_code,
            "amount": amount_vnd,
            "description": description,
            "cancelUrl": self.cancel_url,
            "returnUrl": self.return_url,
            "signature": signature,
        }
        headers = {
            "x-client-id": self._client_id,
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        try:
            if self._http_client is not None:
                response = self._http_client.post(
                    PAYOS_CREATE_PAYMENT_URL,
                    json=payload,
                    headers=headers,
                    timeout=self._timeout_seconds,
                )
            else:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(
                        PAYOS_CREATE_PAYMENT_URL,
                        json=payload,
                        headers=headers,
                    )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise BillingProviderRequestError("billing provider request failed") from exc

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, dict) or body.get("code") != "00":
            raise BillingProviderRequestError("billing provider rejected the request")

        checkout_url = data.get("checkoutUrl")
        if not isinstance(checkout_url, str) or not checkout_url.startswith("https://"):
            raise BillingProviderRequestError("billing provider returned an invalid response")

        payment_link_id = data.get("paymentLinkId")
        if payment_link_id is not None and not isinstance(payment_link_id, str):
            payment_link_id = str(payment_link_id)

        return PaymentLinkResult(
            checkout_url=checkout_url,
            payment_link_id=payment_link_id,
            sanitized_payload={
                "code": body.get("code"),
                "description": body.get("desc"),
                "provider_status": data.get("status"),
                "provider_order_code": data.get("orderCode"),
            },
        )
