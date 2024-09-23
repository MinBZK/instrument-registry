import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from task_registry.lifespan import CACHED_DATA

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "/",
    summary="Overview of all the Instruments in the Task Registry",
    description="This endpoint returns a JSON with all the Instruments in the Task Registry.",
    responses={200: {"description": "JSON with all the instruments."}},
)
async def get_root() -> JSONResponse:
    return JSONResponse(content=CACHED_DATA["index"])
