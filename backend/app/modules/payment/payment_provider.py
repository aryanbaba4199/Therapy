"""Payment provider abstraction layer and mock gateway implementation."""

import hashlib
import hmac
import uuid
from abc import ABC, abstractmethod
from typing import Any

from app.modules.payment.payment_constants import PaymentProviderName


class PaymentOrderResult:
    """Standardized response from creating an order with a payment gateway."""

    def __init__(self, provider_order_id: str, amount_minor: int, currency: str, client_secret: str | None = None) -> None:
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
