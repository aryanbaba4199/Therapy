# Booking Feature Module

## Architectural Responsibility & 7-File Convention

Every backend feature module in this platform MUST follow this strict 7-file separation of concerns:

1. `booking_route.py`: HTTP routing declarations only. No business logic.
2. `booking_controller.py`: HTTP-level orchestration, parameter parsing, delegating to services.
3. `booking_service.py`: Core domain and business logic. Independent of HTTP transport.
4. `booking_repository.py`: Database access layer (MongoDB queries via Motor).
5. `booking_schema.py`: Pydantic request payloads and response validation schemas.
6. `booking_model.py`: Internal MongoDB document and entity representations.
7. `booking_dependency.py`: Feature-specific FastAPI dependency injectors (`Depends`).

> **Note**: Do not implement business logic in Phase 1. This directory serves as the architectural scaffold for subsequent phases.
