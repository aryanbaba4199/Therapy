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

---

## 8. Phase 7 — Session Management & Therapist Portal Architecture

### Domain Separation & Operational Lifecycle
1. **Confirmed Booking to Scheduled Session Invariant**:
   - The platform strictly maintains a **1:1 invariant** between a confirmed booking and an operational therapy session, enforced via a MongoDB unique index on `booking_id`.
   - Upon booking confirmation (`confirm_booking`), `SessionService.create_session_for_booking()` is invoked idempotently to automatically instantiate the session in `SCHEDULED` status.
   - If a booking is cancelled, `SessionService.cancel_session_for_booking()` transitions the operational session directly to `CANCELLED`.
2. **Session Lifecycle State Machine**:
   - `scheduled`: Session is confirmed and awaiting its scheduled time window.
   - `ready`: Within the pre-session startup window (`session_start_window_minutes = 15`).
   - `in_progress`: Therapist has initiated the session (`start_session_atomic`). Concurrency-safe atomic transition ensures that concurrent calls can only start the session once.
   - `completed`: Therapist finishes the consultation (`complete_session_atomic`), setting `ended_at` timestamp.
   - `cancelled` / `no_show`: Terminal states for unattended or cancelled consultations.
3. **Clinical Notes Isolation & Strict Privacy Boundary**:
   - Decoupled `session_notes` collection separate from `sessions` to enforce least-privilege data isolation and clinical confidentiality.
   - Notes consist of two distinct fields:
     - `summary`: High-level consultation overview, takeaways, and recommended homework visible to both client and therapist.
     - `private_notes`: Highly confidential clinical hypotheses, diagnostic considerations, and observations accessible **exclusively** to the assigned therapist and authorized clinical admins.
   - The client endpoint `/api/v1/sessions/{id}/notes/client` uses `ClientSessionNoteResponse` which completely omits `private_notes`.
   - IDOR prevention: All mutations and reads verify that caller is the session's assigned therapist or has admin roles.
4. **Therapy Goals System**:
   - Client goal management (`therapy_goals` collection) tracks progress across consultations with statuses: `active`, `completed`, and `archived`.
   - Therapists can define action plans, milestones, and homework strategies linked to the client and session.
5. **Therapist Portal UI**:
   - `/therapist/dashboard`: Operational hub featuring real-time metrics (Today's Agenda, Upcoming, Completed), live session controls (Start/Complete), and quick attendance recording modal.
   - `/therapist/sessions`: Comprehensive filterable consultation ledger by status and date with pagination.
   - `/therapist/sessions/:id`: Deep session detail view with session metadata, attendance controls, Clinical Notes editor (with clear confidentiality badges), and Therapy Goals management.
   - `/my-sessions`: Client-facing consultation history displaying session status, schedule, mode, and shared summary notes (with zero exposure to private notes).
   - 100% trilingual localization across English (`en`), Malayalam (`ml`), and Tamil (`ta`).

---

## 9. Phase 8 — Reviews, Feedback & Customer Support Architecture

### Domain Overview & Operational Design
1. **Post-Session Reviews & Aggregated Ratings**:
   - **1-Review-Per-Session Invariant**: Strictly enforced at the database level with a MongoDB unique index on `session_id`.
   - **Eligibility & Verification**: Caller must be an authenticated client owning the completed therapy session. Only sessions in `COMPLETED` status are eligible for review.
   - **Rating Metrics**: Integer score between 1 and 5 (`$1 \le \text{rating} \le 5$`). Optional structured feedback includes review comment, client display name (with option for anonymization `Anonymous Client`), and session tags.
   - **Aggregated Ratings Calculation**: The `ReviewRepository.get_therapist_rating_summary()` executes an efficient MongoDB `$facet` aggregation pipeline computing:
     - `average_rating`: Rounded to 2 decimal places.
     - `review_count`: Total published reviews count.
     - `rating_distribution`: Count of 1-star, 2-star, 3-star, 4-star, and 5-star ratings.
   - **Concurrency Safety**: High-concurrency submissions on the same session are mutually exclusive; exactly 1 review succeeds while subsequent concurrent attempts fail with `409 Conflict` (`REVIEW_ALREADY_EXISTS`).
   - **Public vs Client Endpoints**:
     - `GET /api/v1/reviews/therapist/{therapist_id}`: Public listing of published reviews.
     - `GET /api/v1/reviews/therapist/{therapist_id}/summary`: Public summary with rating distribution.
     - `GET /api/v1/reviews/my`: Authenticated client's review history.
     - `POST /api/v1/reviews`: Authenticated submission with eligibility validation.

2. **Customer Support & Ticket System**:
   - **Dedicated Ticket Ledger**: Tickets stored in `support_tickets` collection with auto-generated sequential ticket numbers (`TKT-YYYYMMDD-XXXX`).
   - **Ticket Categories & Priorities**:
     - Categories: `booking`, `payment`, `therapist`, `session`, `package`, `account`, `technical`, `other`.
     - Priorities: `low`, `normal`, `high`, `urgent`.
     - Status Lifecycle: `open` -> `in_progress` -> `waiting_for_user` -> `resolved` -> `closed`.
   - **Strict IDOR Reference Verification**:
     - When submitting tickets with contextual entity references (`booking_id`, `payment_id`, `package_id`, `session_id`), the `SupportService` verifies ownership against the corresponding collections. If a user attempts to reference a resource belonging to another client or therapist, the request is rejected with `403 Forbidden` (`SUPPORT_TICKET_REFERENCE_FORBIDDEN`).
   - **Scalable Messaging & Internal Notes Isolation**:
     - Support conversation threads are stored in a dedicated `support_messages` collection indexed on `(ticket_id, created_at)`.
     - `is_internal_note`: Support agents and staff can post internal deliberations that are strictly hidden from client-facing responses and visible only to staff roles.
   - **Staff Assignment Workflows**:
     - Staff members can assign tickets (`assign_ticket`), update statuses (`update_ticket_status`), and collaborate within conversation threads.

3. **Frontend Integration & Trilingual Support**:
   - **Review System UI**:
     - `ReviewFormModal.tsx`: Interactive review dialog with 5-star interactive rating input, character validation, and anonymous toggles.
     - `TherapistRatingSummary.tsx` & `ReviewCard.tsx`: Rich rating summaries and published feedback cards embedded into `TherapistDetailPage.tsx`.
     - `MyReviewsPage.tsx`: Client portal page (`/my-reviews`) tracking submitted reviews.
     - `ClientSessionHistoryPage.tsx`: Quick "Review Consultation" action available on completed sessions.
   - **Support Center UI**:
     - `SupportCenterPage.tsx`: Filterable ticket overview (`/support`) with category tabs, status indicators, and modal ticket creation (`CreateTicketModal.tsx`).
     - `TicketDetailPage.tsx`: Deep conversation viewer (`/support/tickets/:ticketId`) displaying chronological client and staff messages, entity reference cards, and dynamic reply composer.
   - **Global Accessibility & Strict Type Safety**:
     - Integrated into `MainLayout.tsx` header navigation and React Router.
     - 100% trilingual localization in English (`en`), Malayalam (`ml`), and Tamil (`ta`).
     - Zero TypeScript errors (`npm run type-check`), zero lint violations (`npm run lint`), Prettier formatted (`npm run format:check`), and production build passing (`npm run build`).

---

## 10. Phase 9 — Operations, Administration & First Responder Architecture

### Domain Overview & Operational Design
1. **Role & Permission Model**:
   - **Extended Role Enumeration**: `UserRole` contains `user`, `therapist`, `staff`, `first_responder`, `admin`, and `super_admin`.
   - **Granular Permissions Architecture**: `Permission` enum defines explicit actions across 7 capability domains:
     - Dashboard: `dashboard:view`
     - Users: `users:read`, `users:update`, `users:suspend`, `roles:manage`
     - Therapists: `therapists:read`, `therapists:verify`, `therapists:manage`
     - Bookings & Sessions: `bookings:read`, `bookings:manage`, `sessions:read`
     - Payments & Commercial: `payments:read`, `offers:manage`, `packages:manage`
     - Support: `support:read`, `support:assign`, `support:resolve`, `support:escalate`
     - Leads: `leads:read`, `leads:manage`, `leads:assign`
     - Moderation: `reviews:moderate`
     - Audit: `audit:read`
   - **Deterministic Mapping**: `ROLE_PERMISSIONS` dictionary maps roles to allowed permission sets. `super_admin` has universal access; `admin` has operational oversight; `staff` has read and support execution privileges; `first_responder` specializes in prospect triage and ticket escalation.

2. **Operational Dashboard Aggregations**:
   - High-level platform health metrics are computed using targeted MongoDB index scans and aggregation pipelines:
     - `today_bookings`: Bookings created between 00:00:00 and 23:59:59 today.
     - `upcoming_sessions`: Consultations in `scheduled` or `ready` status with `start_at >= now()`.
     - `completed_sessions`: Lifetime successfully held sessions.
     - `active_therapists` & `pending_verification_therapists`: Licensed vs onboarding clinical capacity.
     - `pending_support_tickets`: Unresolved inquiries in `open`, `in_progress`, or `waiting_for_user`.
     - `failed_payments_count`: Transactions flagged as failed for commercial triage.
     - `total_revenue_minor`: `$sum` aggregation across all `paid` payment transactions.
     - `new_leads_count`: Prospective leads awaiting initial contact.

3. **User Management & Destructive Protection**:
   - Operational endpoints allow staff/admin to search and filter platform users by role and status.
   - **Super Admin Protection**:
     - Non-super admins cannot suspend Super Admin accounts.
     - Elevating users to `admin` or `super_admin`, or modifying Super Admin roles, strictly requires caller to hold `super_admin`.
     - Non-compliance fails with `403 Forbidden` (`OPS_ROLE_CHANGE_FORBIDDEN`).

4. **First Responder Triage & Lead Lifecycle**:
   - `leads` collection tracks prospective inquiries prior to account registration:
     - Status State Machine: `new` &rarr; `contacted` (auto-records `last_contacted_at`) &rarr; `follow_up` &rarr; `converted` &rarr; `lost`.
     - Acquisition Sources: `website`, `helpline`, `referral`, `campaign`, `other`.
     - Assignment & Handoffs: Leads can be assigned and reassigned between staff and first responders with mandatory reason logging.
     - Conversion: Seamless transition linking `converted_user_id` to an existing client user record.

5. **Immutable Operational Audit Trail**:
   - `audit_logs` collection provides an append-only ledger of privileged administrative mutations.
   - Every state-altering action emits an audit record capturing:
     - `actor_id` and `actor_role`
     - `action` (`AuditAction` enum)
     - `resource_type` and `resource_id`
     - Sanitized `metadata` (capturing previous vs new states and operational reasons without secrets/PII)
     - Distributed trace `request_id` from ContextVar middleware
     - UTC `created_at` timestamp
   - Read-only queries supported by indexes on `(created_at DESC)`, `(actor_id, created_at)`, `(resource_type, resource_id, created_at)`.

6. **Frontend Operations UI**:
   - Route Protection: `/operations/*` protected by `RoleProtectedRoute` admitting `staff`, `first_responder`, `admin`, and `super_admin`.
   - Pages Built:
     - `AdminDashboardPage.tsx`: Metric indicators and live counters.
     - `UserManagementPage.tsx`: Searchable user table, status modal (suspend/activate), and role assignment dialog.
     - `TherapistOperationsPage.tsx`: Practitioner verification queue with credential review.
     - `LeadManagementPage.tsx`: Inbound triage ledger, create lead dialog, assign agent, and convert to client.
     - `BookingOperationsPage.tsx`: Cross-cutting appointment ledger with client/therapist lookups.
     - `PaymentOperationsPage.tsx`: Commercial ledger with failure diagnostics and transaction codes.
     - `FirstResponderDashboardPage.tsx`: Crisis triage queue and incoming lead cards.
     - `AuditLogPage.tsx`: Chronological audit trail table with metadata inspection.
   - Fully localized in English (`en`), Malayalam (`ml`), and Tamil (`ta`) (`operations.json`).
