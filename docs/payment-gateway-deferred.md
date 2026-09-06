# Deferred Payment Gateway Integration Specification

## 1. Overview & Decision Status

The production payment gateway for the Therapy (Oppam) platform has **not yet been selected**.
Potential candidates under commercial and regulatory evaluation include:
* **Razorpay** (India domestic cards, UPI, netbanking)
* **Cashfree** (India domestic UPI, cards)
* **PhonePe PG** (India domestic UPI)
* **Stripe** (International / NRI clients)

Because the commercial contract and gateway selection are pending, all provider-specific implementations have been intentionally **deferred** to avoid speculative technical debt or premature vendor lock-in.

---

## 2. Gateway-Independent Commercial Invariants

The platform enforces strict commercial integrity invariants completely independent of any payment provider:

1. **Package Entitlement Idempotency**:
   * MongoDB unique sparse index: `idx_user_packages_payment_id_unique` on `user_packages.payment_id`.
   * Exactly one `UserPackageInDB` entitlement is created per commercial payment ID.
   * Concurrent or repeated calls to `fulfill_package_purchase()` return the existing entitlement idempotently without allocating duplicate credits.

2. **Decoupled Payment vs Fulfillment State**:
   * `PaymentStatus`: `created`, `pending`, `authorized`, `paid`, `failed`, `cancelled`, `refunded`.
   * `FulfillmentStatus`: `pending`, `processing`, `fulfilled`, `failed`.
   * The platform distinguishes the monetary confirmation (`status == "paid"`) from the business fulfillment (`fulfillment_status == "fulfilled"`).
   * If a client verification fails mid-flight or a webhook arrives, the system safely re-attempts commercial fulfillment until `fulfillment_status == "fulfilled"`.

3. **Package Credit & Offer Usage Safety**:
   * Offer / coupon usage increment is atomically tracked and tied to the commercial transaction.
   * Package session redemptions are atomically decremented.

4. **Provider Abstraction Contract**:
   * The system depends exclusively on the [`PaymentProvider`](../backend/app/modules/payment/payment_provider.py) interface:
     * `create_order(...) -> ProviderOrderResponse`
     * `verify_payment_signature(...) -> bool`
     * `verify_webhook_signature(...) -> bool`
   * In development and testing, `MockPaymentProvider` satisfies this interface with cryptographic HMAC signatures.

---

## 3. Explicitly Deferred Work Items

When the production payment gateway is selected in Phase 10 or later, the following tasks will be implemented:

1. **Provider SDK Integration**:
   * Install official provider SDK or implement REST API client with exponential backoff.
2. **Provider-Specific Webhook Handlers**:
   * Implement real signature verification (e.g. Razorpay webhook secret, Stripe webhook signatures).
   * Map provider-specific webhook events (`payment.captured`, `charge.succeeded`, etc.) to internal events.
3. **Frontend Gateway SDK Checkout**:
   * Integrate provider checkout modal/SDK in `frontend/src/features/payment/`.
4. **Reconciliation & Settlement Automation**:
   * Batch reconciliation jobs comparing gateway settlement reports against internal ledger.
5. **PCI-DSS & Compliance Audit**:
   * Security hardening for production payment processing.
