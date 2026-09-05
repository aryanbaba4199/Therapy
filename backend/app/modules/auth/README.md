# Auth Feature Module

## Architectural Responsibility & 7-File Convention

Every backend feature module in this platform MUST follow this strict 7-file separation of concerns:

1. `auth_route.py`: HTTP routing declarations only. No business logic.
2. `auth_controller.py`: HTTP-level orchestration, parameter parsing, delegating to services.
3. `auth_service.py`: Core domain and business logic. Independent of HTTP transport.
4. `auth_repository.py`: Database access layer (MongoDB queries via Motor).
5. `auth_schema.py`: Pydantic request payloads and response validation schemas.
6. `auth_model.py`: Internal MongoDB document and entity representations.
7. `auth_dependency.py`: Feature-specific FastAPI dependency injectors (`Depends`).

> **Note**: Do not implement business logic in Phase 1. This directory serves as the architectural scaffold for subsequent phases.
