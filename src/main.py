from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import health_router
from src.api.router import router as api_router
from src.auth.router import router as auth_router
from src.core.config import settings
from src.core.constants import Environment

# Create the FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    debug=settings.ENVIRONMENT == Environment.LOCAL,
)


# Add CORS middleware if there are allowed origins specified in the settings
if settings.ALLOWED_CORS_ORIGINS:
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.ALLOWED_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Include the API routers with the specified prefix
app.include_router(router=health_router)
app.include_router(router=auth_router, prefix=settings.API_URL)  # Public routes (auth)
app.include_router(router=api_router, prefix=settings.API_URL)  # Protected routes (requires auth)
