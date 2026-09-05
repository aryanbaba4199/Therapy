# Therapist Feature Module

## Architectural Responsibility & 7-File Convention

Every backend feature module in this platform MUST follow this strict 7-file separation of concerns:

1. `therapist_route.py`: HTTP routing declarations only. No business logic.
2. `therapist_controller.py`: HTTP-level orchestration, parameter parsing, delegating to services.
3. `therapist_service.py`: Core domain and business logic. Independent of HTTP transport.
4. `therapist_repository.py`: Database access layer (MongoDB queries via Motor).
5. `therapist_schema.py`: Pydantic request payloads and response validation schemas.
6. `therapist_model.py`: Internal MongoDB document and entity representations.
7. `therapist_dependency.py`: Feature-specific FastAPI dependency injectors (`Depends`).

> **Note**: Do not implement business logic in Phase 1. This directory serves as the architectural scaffold for subsequent phases.
