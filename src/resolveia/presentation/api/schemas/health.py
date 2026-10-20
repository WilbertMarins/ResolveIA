"""Schemas for operational health endpoints."""

from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    """Stable liveness response."""

    status: Literal["alive"] = "alive"


class ReadinessChecks(BaseModel):
    """Public status of required dependencies."""

    database: Literal["available", "unavailable"]
    object_storage: Literal["available", "unavailable"]


class ReadinessResponse(BaseModel):
    """Stable readiness response."""

    status: Literal["ready", "not_ready"]
    checks: ReadinessChecks
