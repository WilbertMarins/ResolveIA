"""Operational health routes."""

import asyncio
from collections.abc import Mapping
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from resolveia.application.ports import ReadinessCheck
from resolveia.presentation.api.dependencies import get_readiness_checks
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
    readiness_checks: Annotated[
        Mapping[str, ReadinessCheck],
        Depends(get_readiness_checks),
    ],
) -> ReadinessResponse:
    """Report whether required infrastructure is available."""
    database_available, storage_available = await asyncio.gather(
        readiness_checks["database"].check(),
        readiness_checks["object_storage"].check(),
    )
    checks = ReadinessChecks(
        database="available" if database_available else "unavailable",
        object_storage="available" if storage_available else "unavailable",
    )
    if database_available and storage_available:
        return ReadinessResponse(status="ready", checks=checks)

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="not_ready", checks=checks)
