# Oppam Counselling Platform — Phase 1 Foundation

A production-grade online therapy and counselling platform clone inspired by Oppam (Kerala's First 24/7 Online Counselling Platform).

---

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Motor** (Asynchronous MongoDB driver)
- **Pydantic v2** & **Pydantic Settings**
- **uv** for dependency management
- **Ruff** for high-speed linting and code formatting
- **MyPy** for strict static typing
- **Pytest** & **HTTPX** for asynchronous test coverage

### Frontend
- **React 19** + **TypeScript** (Strict Mode, Zero `any`)
- **Vite** bundler
- **Redux Toolkit** & **RTK Query** for API communication
- **Material UI (MUI)** for accessible UI primitives
- **Tailwind CSS** for responsive utility-first layouts
- **i18next** & **react-i18next** for trilingual localization (**English**, **Malayalam മലയാളം**, **Tamil தமிழ்**)
- **React Icons** for UI iconography

---

## Getting Started

### Prerequisites
- Node.js v20+ & npm
- Python 3.11+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- MongoDB (optional for Phase 1 health check; system runs gracefully in disconnected mode)

### 1. Backend Setup
```bash
cd backend

# Install dependencies with uv
uv sync

# Run tests
uv run pytest -v

# Run linting and type checking
uv run ruff check .
uv run mypy app tests

# Start development server
uv run uvicorn app.main:create_app --factory --reload --port 8000
```
Backend API will be available at `http://localhost:8000/api/v1/health` with documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run type check and linter
npm run type-check
npm run lint

# Run production build
npm run build

# Start development server
npm run dev
```
Frontend will be available at `http://localhost:5173`.

---

## Architectural Rules & Standards

1. **Feature Module Convention (7 Files)**:
   Every backend feature must separate concerns into:
   - `<feature>_route.py`
   - `<feature>_controller.py`
   - `<feature>_service.py`
   - `<feature>_repository.py`
   - `<feature>_schema.py`
   - `<feature>_model.py`
   - `<feature>_dependency.py`

2. **Internationalization (Zero Hardcoded Text)**:
   - All user-facing text is translated across `en`, `ml`, and `ta`.
   - Namespaces: `common`, `navigation`, `auth`, `validation`.
   - Never write hardcoded UI strings; always use `t("namespace.key")`.

3. **Zero `any` in TypeScript**:
   - TypeScript configured in strict mode with explicit forbidden `any`.
   - Unknown types must use `unknown` with safe narrowing.

4. **Response Envelope**:
   - All HTTP responses adhere to the standard envelope:
   ```json
   {
     "success": true,
     "message": "...",
     "data": { ... },
     "meta": null,
     "error": null,
     "request_id": "..."
   }
   ```

---

## Database Seeding

To seed the initial Super Admin user:

```bash
cd backend
PYTHONPATH=. ./.venv/bin/python scripts/seed_super_admin.py
# Or using uv:
# PYTHONPATH=. uv run python scripts/seed_super_admin.py
```
