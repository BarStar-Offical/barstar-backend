# API Router Developer Guide

This document explains how the API router works in this module and how to expand it for new endpoints.

## Overview

The router is defined in `routes.py` and is responsible for handling HTTP requests to the API. It uses FastAPI's `APIRouter` to organize endpoints by functionality. Dependencies and authentication can be managed via `deps.py`.

## Structure

- `routes.py`: Contains the main router and endpoint definitions.
- `deps.py`: Provides reusable dependencies (e.g., authentication, database session).
- `__init__.py`: Makes the module importable.

## How the Router Works

1. **Router Initialization**: An instance of `APIRouter` is created in `routes.py`.
2. **Endpoint Definition**: Endpoints are added to the router using decorators like `@router.get`, `@router.post`, etc.
3. **Dependency Injection**: Common dependencies (e.g., DB session, user authentication) are injected using FastAPI's `Depends`.
4. **Inclusion in Main App**: The router is included in the main FastAPI app (usually in `main.py`) via `app.include_router()`.

## Expanding the Router

To add new endpoints:

1. **Define the Endpoint**: In `routes.py`, use the appropriate decorator (`@router.get`, `@router.post`, etc.) and implement the handler function.
2. **Add Dependencies**: If your endpoint needs authentication or other dependencies, import them from `deps.py` and use `Depends`.
3. **Update Schemas**: If your endpoint returns or accepts new data models, define them in the `schemas/` directory.
4. **Update Models**: If you need new database tables, update the models in `models/` and run Alembic migrations.
5. **Test Your Endpoint**: Add tests in the `tests/` directory to ensure your endpoint works as expected.

## Example: Adding a New Endpoint

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_db
from app.schemas.user import User

router = APIRouter()

@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db=Depends(get_db)):
    # ...implementation...
    pass
```

## Best Practices

- Keep endpoint logic minimal; delegate business logic to service modules.
- Use Pydantic schemas for request/response validation.
- Reuse dependencies from `deps.py`.
- Document endpoints with docstrings.

## Testing with Swagger UI

FastAPI automatically generates interactive API documentation using Swagger UI (OpenAPI). This allows you to test endpoints directly from your browser.

### Accessing Swagger UI

1. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open Swagger UI** in your browser:
   ```
   http://localhost:8000/docs
   ```

### Using Swagger UI to Test Endpoints

1. **Browse Endpoints**: All available endpoints are listed with their HTTP methods (GET, POST, PUT, DELETE, etc.).

2. **Expand an Endpoint**: Click on any endpoint to see its details, including:
   - Request parameters
   - Request body schema
   - Response models
   - Status codes

3. **Try it Out**:
   - Click the "Try it out" button
   - Fill in required parameters and request body
   - Click "Execute" to send the request
   - View the response, including status code, headers, and body

4. **Authentication**: If endpoints require authentication:
   - Click the "Authorize" button at the top
   - Enter your credentials or API token
   - All subsequent requests will include the authentication

### Alternative: ReDoc

FastAPI also provides ReDoc documentation at:
```
http://localhost:8000/redoc
```

ReDoc offers a cleaner, read-only view of your API documentation.

## References
- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/routing/)
- [Pydantic Schemas](https://docs.pydantic.dev/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

---
For further questions, contact the backend team or check the main project README.
