from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> dict[str, str]:
    """Return application health status."""

    return {"status": "ok"}
