"""Operational readiness port."""

from typing import Protocol


class ReadinessCheck(Protocol):
    """Report whether required infrastructure is available."""

    async def check(self) -> bool:
        """Return true when the application is ready to receive traffic."""
        ...
