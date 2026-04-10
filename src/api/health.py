from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=["Health"])


# Health check application
@health_router.get("/", summary="Application Health Checkup")
async def app_health() -> dict[str, str]:
    """
    ### Application Health check
    This endpoint returns the status of the application.
    """
    return {"status": "ok"}
