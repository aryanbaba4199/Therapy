# User Feature Module

## Architectural Responsibility & 7-File Convention

Every backend feature module in this platform MUST follow this strict 7-file separation of concerns:

1. `user_route.py`: HTTP routing declarations only. No business logic.
2. `user_controller.py`: HTTP-level orchestration, parameter parsing, delegating to services.
3. `user_service.py`: Core domain and business logic. Independent of HTTP transport.
4. `user_repository.py`: Database access layer (MongoDB queries via Motor).
5. `user_schema.py`: Pydantic request payloads and response validation schemas.
6. `user_model.py`: Internal MongoDB document and entity representations.
7. `user_dependency.py`: Feature-specific FastAPI dependency injectors (`Depends`).

> **Note**: Do not implement business logic in Phase 1. This directory serves as the architectural scaffold for subsequent phases.
