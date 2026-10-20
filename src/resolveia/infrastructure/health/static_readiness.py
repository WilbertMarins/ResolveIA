"""Deterministic readiness adapter for explicitly injected infrastructure."""


class StaticReadinessCheck:
    """Return a fixed readiness result without external I/O."""

    def __init__(self, available: bool) -> None:
        self._available = available

    async def check(self) -> bool:
        """Return the configured result."""
        return self._available
