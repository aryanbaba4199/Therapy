"""Payment provider abstraction layer, Mock gateway, and Razorpay production implementation."""

import hashlib
import hmac
import uuid
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.common.exceptions.app_exceptions import BadRequestException
from app.common.exceptions.error_codes import ErrorCode
from app.modules.payment.payment_constants import PaymentProviderName


class PaymentOrderResult:
    """Standardized response from creating an order with a payment gateway."""

    def __init__(
        self,
        provider_order_id: str,
        amount_minor: int,
        currency: str,
        client_secret: str | None = None,
    ) -> None:
        self.provider_order_id = provider_order_id
        self.amount_minor = amount_minor
        self.currency = currency
        self.client_secret = client_secret


class PaymentProvider(ABC):
    """Abstract interface decouple commercial transactions from payment vendors."""

    @property
    @abstractmethod
    def name(self) -> PaymentProviderName:
        """Name identifier of the provider."""
        ...

    @abstractmethod
    async def create_order(
        self, amount_minor: int, currency: str, receipt: str, notes: dict[str, Any] | None = None
    ) -> PaymentOrderResult:
        """Generate provider order."""
        ...

    @abstractmethod
    def verify_payment_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        """Verify client-submitted payment signature."""
        ...

    @abstractmethod
    def verify_webhook_signature(
        self, payload_body: bytes, signature_header: str, secret: str
    ) -> bool:
        """Verify authenticity of incoming webhook payload."""
        ...


class MockPaymentProvider(PaymentProvider):
    """Production-grade mock payment provider for local dev and automated tests."""

    def __init__(self, secret_key: str = "mock_secret_key_therapy_2026") -> None:
        self.secret_key = secret_key

    @property
    def name(self) -> PaymentProviderName:
        return PaymentProviderName.MOCK

    async def create_order(
        self, amount_minor: int, currency: str, receipt: str, notes: dict[str, Any] | None = None
    ) -> PaymentOrderResult:
        provider_order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
        return PaymentOrderResult(
            provider_order_id=provider_order_id,
            amount_minor=amount_minor,
            currency=currency,
            client_secret=f"secret_{provider_order_id}",
        )

    def generate_signature(self, order_id: str, payment_id: str) -> str:
        """Generate expected HMAC signature for test assertions and simulation."""
        message = f"{order_id}|{payment_id}".encode()
        return hmac.new(self.secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()

    def verify_payment_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        expected = self.generate_signature(order_id, payment_id)
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(
        self, payload_body: bytes, signature_header: str, secret: str
    ) -> bool:
        computed = hmac.new(secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature_header)


class RazorpayPaymentProvider(PaymentProvider):
    """Production Razorpay implementation using asynchronous HTTP client."""

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        webhook_secret: str,
        api_base_url: str = "https://api.razorpay.com/v1",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.key_id = key_id
        self.key_secret = key_secret
        self.webhook_secret = webhook_secret
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> PaymentProviderName:
        return PaymentProviderName.RAZORPAY

    async def create_order(
        self, amount_minor: int, currency: str, receipt: str, notes: dict[str, Any] | None = None
    ) -> PaymentOrderResult:
        """Create a Razorpay order via the Orders REST API."""
        payload = {
            "amount": amount_minor,
            "currency": currency.upper(),
            "receipt": receipt[:40],
            "notes": {str(k): str(v) for k, v in (notes or {}).items() if v is not None},
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/orders",
                    json=payload,
                    auth=(self.key_id, self.key_secret),
                )
            except Exception as exc:
                raise BadRequestException(
                    message=f"Razorpay network communication failed: {exc}",
                    code=ErrorCode.PAYMENT_GATEWAY_ERROR,
                ) from exc

        if response.status_code != 200:
            err_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            description = err_data.get("error", {}).get("description", response.text)
            raise BadRequestException(
                message=f"Razorpay order creation failed: {description}",
                code=ErrorCode.PAYMENT_GATEWAY_ERROR,
            )

        data = response.json()
        provider_order_id = data.get("id")
        if not provider_order_id:
            raise BadRequestException(
                message="Razorpay returned empty order ID",
                code=ErrorCode.PAYMENT_GATEWAY_ERROR,
            )

        return PaymentOrderResult(
            provider_order_id=provider_order_id,
            amount_minor=int(data.get("amount", amount_minor)),
            currency=str(data.get("currency", currency)),
        )

    def verify_payment_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        """Verify client-submitted Razorpay payment signature: HMAC-SHA256 of order_id|payment_id."""
        if not self.key_secret:
            return False
        message = f"{order_id}|{payment_id}".encode()
        computed = hmac.new(self.key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    def verify_webhook_signature(
        self, payload_body: bytes, signature_header: str, secret: str
    ) -> bool:
        """Verify raw payload bytes against Razorpay webhook signature header using configured secret."""
        target_secret = secret or self.webhook_secret
        if not target_secret or not signature_header:
            return False
        computed = hmac.new(target_secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature_header)
