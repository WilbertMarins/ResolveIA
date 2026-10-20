"""Operational health routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from resolveia.application.ports import ReadinessCheck
from resolveia.presentation.api.dependencies import get_readiness_check
from resolveia.presentation.api.schemas import (
    LivenessResponse,
    ReadinessChecks,
    ReadinessResponse,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=LivenessResponse)
async def get_liveness() -> LivenessResponse:
    """Report process liveness without checking external dependencies."""
    return LivenessResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def get_readiness(
    response: Response,
    readiness_check: Annotated[ReadinessCheck, Depends(get_readiness_check)],
) -> ReadinessResponse:
    """Report whether required infrastructure is available."""
    if await readiness_check.check():
        return ReadinessResponse(
            status="ready",
            checks=ReadinessChecks(database="available"),
        )

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="not_ready",
        checks=ReadinessChecks(database="unavailable"),
    )
