# Oppam Counselling Platform — System Architecture & Engineering Standards

## 1. Overview & Architectural Philosophy

The Oppam Counselling Platform is designed with a strict **feature-first, domain-driven architecture**.
The platform operates with multi-language requirements (English, Malayalam, Tamil) as a **first-class citizen**, zero-tolerance for explicit `any` in frontend TypeScript, and unified error/response contracts across FastAPI and Redux Toolkit Query.

---

## 2. Backend Architecture (Python + FastAPI + MongoDB)

### Directory Structure
```
backend/
├── app/
│   ├── main.py                  # FastAPI application factory with async lifespan
│   ├── core/
│   │   ├── config.py            # Central Pydantic BaseSettings (strongly typed, environment-driven)
│   │   ├── logging.py           # Structured logging with sensitive data sanitization
│   │   └── security.py          # Security primitives (HMAC, hashing, expiry computation)
│   ├── database/
│   │   └── mongodb.py           # Async Motor connection manager with ping diagnostics & DI
│   ├── common/
│   │   ├── exceptions/          # AppException, BusinessException, NotFoundException, ErrorCode
│   │   ├── responses/           # Standardized ApiResponse[T] envelope models
│   │   ├── pagination/          # PaginationParams, PaginationMeta, PaginatedData[T]
│   │   ├── enums/               # Environment, SupportedLanguage (StrEnum)
│   │   ├── types/               # JsonDict, JsonMapping
│   │   └── utils/               # UTC timezone-aware datetime utilities
│   ├── middleware/
│   │   ├── request_id_middleware.py   # ContextVar request ID generator & X-Request-ID propagation
│   │   ├── logging_middleware.py      # Latency & access logger
│   │   ├── exception_middleware.py    # Global exception handlers (AppException, ValidationError, 500)
│   │   └── middleware_config.py       # Pipeline setup (CORS, RequestId, Logging, Exceptions)
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Central versioned router (/api/v1)
│   │       └── endpoints/
│   │           └── health.py    # GET /api/v1/health operational diagnostics
│   └── modules/                 # Future Feature Modules
│       ├── auth/
│       ├── user/
│       ├── therapist/
│       ├── availability/
│       ├── booking/
│       ├── payment/
│       ├── package/
│       ├── offer/
│       ├── session/
│       ├── review/
│       ├── support/
│       └── operations/
└── tests/
    ├── conftest.py              # Test fixtures with ASGI AsyncClient
    ├── api/                     # API integration tests
    └── unit/                    # Unit tests for config, exceptions, envelopes
```

### Feature Module 7-File Separation Rule
Every feature module implemented in subsequent phases MUST adhere to the following 7-file separation:
1. `<feature>_route.py`: HTTP path declarations and endpoint definitions only.
2. `<feature>_controller.py`: HTTP parameter extraction and service orchestration.
3. `<feature>_service.py`: Pure business and domain logic.
4. `<feature>_repository.py`: Async MongoDB data access via Motor.
5. `<feature>_schema.py`: Pydantic request payloads and response validation schemas.
6. `<feature>_model.py`: Internal MongoDB document and database entities.
7. `<feature>_dependency.py`: Feature-specific FastAPI dependency injectors (`Depends(...)`).

### Standard Response Envelope
All endpoints return the following uniform JSON envelope:
```json
{
  "success": true,
  "message": "Platform health check completed",
  "data": { ... },
  "meta": null,
  "error": null,
  "request_id": "893c5d8095b244c3bbcf0e811bc027dc"
}
```
Failed requests return `success: false` with structured machine-readable error codes:
```json
{
  "success": false,
  "message": "Resource not found",
  "data": null,
  "meta": null,
  "error": {
    "code": "NOT_FOUND",
    "details": null
  },
  "request_id": "893c5d8095b244c3bbcf0e811bc027dc"
}
```

---

## 3. Frontend Architecture (React + TypeScript + MUI + Tailwind)

### Directory Structure
```
frontend/src/
├── app/                         # App level bootstrapping
├── common/
│   ├── components/              # Cross-feature components (LanguageSwitcher, etc.)
│   ├── hooks/                   # useAppDispatch, useAppSelector
│   ├── types/                   # ApiResponse, ApiErrorDetails
│   ├── constants/               # Global constants
│   └── utils/                   # Shared utility helpers
├── layouts/
│   └── main_layout.tsx          # Responsive layout with Oppam branding, Navbar, Footer
├── routes/
│   ├── router.tsx               # createBrowserRouter route definitions
│   ├── app_routes.tsx           # RouterProvider wrapper
│   └── home_page.tsx            # Initial landing with live health telemetry & i18n
├── store/
│   ├── store.ts                 # configureStore with RTK Query middleware & listener setup
│   ├── root_reducer.ts          # Root reducer combining baseApi and future slices
│   └── api/
│       ├── base_api.ts          # Central baseApi with custom reauth query and headers
│       └── health_api.ts        # Injected health query endpoint
├── i18n/
│   ├── config.ts                # Supported languages (en, ml, ta) and namespaces
│   ├── index.ts                 # i18next instance configuration with detector
│   └── locales/
│       ├── en/                  # common.json, auth.json, navigation.json, validation.json
│       ├── ml/                  # Malayalam translations
│       └── ta/                  # Tamil translations
├── theme/
│   ├── mui_theme.ts             # Oppam design palette (Primary Yellow #FFD336, Dark #191301)
│   └── theme_provider.tsx       # StyledEngineProvider(injectFirst) + ThemeProvider + CssBaseline
└── features/                    # Feature modules (auth, therapist, booking, etc.)
    └── <feature>/
        ├── api/                 # Endpoint injections into baseApi
        ├── components/          # Feature UI components
        ├── hooks/               # Feature custom hooks
        ├── pages/               # Feature route pages
        ├── schemas/             # Zod validation schemas
        ├── types/               # TypeScript interfaces
        ├── constants/           # Feature constants
        └── index.ts             # Public feature exports
```

### Critical Frontend Guardrails
1. **Zero `any` Rule**: No `any`, `as any`, or `Promise<any>` allowed anywhere in the codebase. All unknown types must use `unknown` and be safely narrowed.
2. **Strict i18n Rule**: NO hardcoded user-facing strings. All headings, buttons, labels, error messages, and descriptions MUST use `t("namespace.key")`.
3. **Single State Standard**: RTK Query (`baseApi.injectEndpoints`) manages all server cache and data fetching. Redux Toolkit manages global client state. No secondary fetch libraries.
4. **Single Icon Standard**: `react-icons` exclusively.

---

## 4. Engineering & Quality Standards

| Tool | Scope | Purpose | Command |
| :--- | :--- | :--- | :--- |
| **uv** | Backend | Fast dependency management | `uv sync` |
| **Ruff** | Backend | Ultra-fast linter & formatter | `uv run ruff check .` / `uv run ruff format .` |
| **MyPy** | Backend | Strict static type checking | `uv run mypy app tests` |
| **Pytest** | Backend | Unit & integration testing | `uv run pytest -v` |
| **ESLint** | Frontend | Linting with strict `no-explicit-any` | `npm run lint` |
| **TypeScript**| Frontend | Strict compiler validation | `npm run type-check` |
| **Prettier** | Frontend | Code style formatting | `npm run format` |
| **Vite** | Frontend | Bundling & build validation | `npm run build` |

---

## 5. Phase 4 — Availability & Slot Engine Architecture

### Domain Separation & Responsibility
1. **Recurring Weekly Schedule**: Defined per therapist with day of week (0=Mon to 6=Sun), interval windows (`start_time` - `end_time` in "HH:MM"), timezone (e.g. `Asia/Kolkata`), and allowed `session_modes`.
2. **Date-Specific Exceptions**: Date overrides (`is_unavailable: true` or custom replacement intervals) allowing leaves, holidays, or special clinic hours without polluting recurring rules.
3. **Extra Slots**: Explicit one-off slots added by the therapist.
4. **Deterministic Slot Engine (`slot_engine.py`)**: A pure domain algorithm with zero database and zero HTTP dependencies:
   - Chunking: base intervals divided into slots of `duration_minutes + buffer_minutes`.
   - Precedence: Recurring schedule -> Date exception override -> Extra slots.
   - Timezone Handling: Times parsed in therapist's timezone (`ZoneInfo`), canonical timestamps rendered in timezone-aware UTC ISO.
   - Past Slot Filtering: Slots starting in the past relative to current UTC time are excluded for live bookings.
   - Stable Identifiers: 24-character SHA-256 hex digest of `f"{therapist_id}:{start_at.isoformat()}:{end_at.isoformat()}:{session_mode.value}"`.

### Concurrency & Atomic Reservation Strategy (for Phase 5 Booking)
To guarantee that two users attempting to book the same slot simultaneously cannot create double bookings:
1. When generating slots for discovery, slots are presented as transient entities with status `AVAILABLE`.
2. In Phase 5, booking creation executes an atomic conditional write in MongoDB.
3. A unique compound partial index enforces database-level mutual exclusion, guaranteeing that only the first request succeeds while concurrent attempts encounter duplicate key violations / conflict errors.

---

## 6. Phase 5 — Booking & Reservation Engine Architecture

### Domain Flow & Invariants
1. **Slot Selection & Validation**: Slot ID and timestamp parameters are validated against Phase 4 Slot Engine and therapist status (active & verified).
2. **Atomic Temporary Reservation**:
   - Client creates a temporary hold (`ReservationInDB`) with configurable TTL (`BOOKING_RESERVATION_TTL_SECONDS = 900` / 15 minutes).
   - Protected by MongoDB partial unique index on `("therapist_id", "slot_id")` with `partialFilterExpression: {"status": "active"}`.
   - Any concurrent request trying to hold the same slot hits `DuplicateKeyError`, mapped cleanly to `409 Conflict` (`BOOKING_SLOT_UNAVAILABLE`).
   - If a reservation expires, it is lazily transitioned to `expired`, immediately freeing the partial unique index.
   - Client can cancel an active reservation at any time, returning the slot to the pool.
3. **Idempotent Booking Confirmation**:
   - The user reviews the reservation checkout summary with a real-time countdown timer.
   - Confirmation transitions the reservation from `active` to `converted`, creates an immutable `BookingInDB` record with therapist, client, and pricing snapshots, and sets status to `confirmed`.
   - Idempotency check: Retrying confirmation with the same `reservation_id` returns the already confirmed booking without duplicate charges or database records.
   - Bookings collection enforces a partial unique index on `("therapist_id", "slot_id")` for statuses `["pending", "confirmed"]`.
4. **Availability Filtering**:
   - `AvailabilityService.get_available_slots()` filters out all slots actively reserved (`status="active"` and `expires_at > now`) or confirmed (`status in ["pending", "confirmed"]`).
5. **Booking History & Lifecycle**:
   - Authenticated clients query `/api/v1/bookings` with filters (`upcoming`, `past`, `cancelled`) and pagination metadata.
   - Confirmed bookings can be cancelled with an optional cancellation reason.
   - Strictly prepared for Phase 6 (Payment & Offers) with zero payment leakage.

---

## 7. Phase 6 — Payments, Offers & Packages Architecture

### Domain Flow & Commercial Invariants
1. **Commercial Precision & Currency Handling**:
   - All financial amounts are strictly stored and computed in **integer minor units** (e.g. ₹1,000 = `100000` paise).
   - Zero floating-point arithmetic in monetary balance calculations to prevent fractional cent/paise rounding bugs.
2. **Authoritative Server-Side Price Calculation**:
   - `OfferService.calculate_pricing()` authoritatively computes base price, discounts, and final payable amount.
   - Percentage discounts are capped at `max_discount_minor` if set.
   - Minimum order requirements (`min_order_minor`) are strictly enforced before applying any discount.
   - Atomic coupon redemption: `OfferRepository.increment_usage_atomic()` enforces per-user and global usage quotas.
3. **Package Bundles & Atomic Session Balances**:
   - `PackageProductInDB`: Sellable catalog templates (e.g., "5 Sessions Wellness Bundle").
   - `UserPackageInDB`: Entitlement records created upon verified payment, tracking `total_sessions`, `remaining_sessions`, and expiration timestamp.
   - `PackageRepository.consume_session_atomic()`: Executes atomic `find_one_and_update` on MongoDB with condition `remaining_sessions > 0 and status == "active" and expires_at >= now`. When balance hits 0, package automatically transitions to `exhausted`. Tested under concurrent contention: exactly 1 request succeeds, subsequent ones fail cleanly.
   - When redeeming package sessions for booking, payable amount is ₹0, payment method is marked `package_redemption`, and booking confirms immediately without gateway interaction.
4. **Provider Abstraction & Cryptographic Verification**:
   - `PaymentProvider`: Base interface defining `create_order`, `verify_payment_signature`, and `verify_webhook_signature`.
   - `MockPaymentProvider`: Deterministic HMAC-SHA256 signature generator and validator for local development and CI testing.
   - Webhook processing: Validates incoming HMAC signatures against `PAYMENT_WEBHOOK_SECRET` and reconciles pending payments idempotently.
5. **Frontend Commerce Integration**:
   - Fully localized in English (`en`), Malayalam (`ml`), and Tamil (`ta`).
   - Integrated `BookingCheckoutPage.tsx` with coupon code validation, package session credit redemption selector, payment method choices (UPI, Card, NetBanking), and order breakdown.
   - Catalog browsing via `/packages` (`PackageListPage.tsx`) and balance management via `/packages/my` (`MyPackagesPage.tsx`).
