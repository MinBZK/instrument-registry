from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get(
    "/live",
    summary="Liveness Check",
    description="This endpoint returns the liveness status of the application.",
    responses={200: {"description": "The application is live and running."}},
    response_class=JSONResponse,
)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}
