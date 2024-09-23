import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from task_registry.lifespan import CACHED_DATA

router = APIRouter()

logger = logging.getLogger(__name__)


def _validate_urn(urn: str) -> str:
    if urn not in CACHED_DATA["urn_mapper"]:
        raise HTTPException(status_code=400, detail=f"Invalid urn: {urn}")
    return urn


# Optional parameter 'version' is included, but not used. In a new ticket
# versioning of instruments should be handled.
@router.get(
    "/",
    summary="Get the contents of the specific Instrument by URN",
    description="This endpoint returns a JSON with the contents of a specific Instrument identified by URN"
    " and version.",
    responses={
        200: {"description": "JSON with the specific contents of the Instrument."},
        400: {"description": "The URN does not exist or is not valid."},
    },
)
async def get_instrument(urn: str = Depends(_validate_urn), version: str = "latest") -> JSONResponse:
    return JSONResponse(content=CACHED_DATA["urn_mapper"][urn])
