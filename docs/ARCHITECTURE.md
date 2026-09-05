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
