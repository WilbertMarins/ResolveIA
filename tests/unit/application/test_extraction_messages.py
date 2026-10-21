"""Tests for the versioned extraction message contract."""

from uuid import UUID

import pytest

from resolveia.application.messages import (
    ExtractionRequestedMessage,
    InvalidExtractionMessageError,
)

EVENT_ID = UUID("ad61a936-cedf-4cf9-821c-c4e7c6044996")
DOCUMENT_ID = UUID("d39a3706-fd8e-4c93-b550-221e3b7d8a91")


def test_round_trips_the_versioned_payload() -> None:
    message = ExtractionRequestedMessage(EVENT_ID, DOCUMENT_ID)

    assert ExtractionRequestedMessage.from_payload(message.to_payload()) == message


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "event_id": "invalid",
            "document_id": str(DOCUMENT_ID),
            "contract_version": 1,
        },
        {
            "event_id": str(EVENT_ID),
            "document_id": str(DOCUMENT_ID),
            "contract_version": 2,
        },
    ],
)
def test_rejects_invalid_or_unsupported_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(InvalidExtractionMessageError):
        ExtractionRequestedMessage.from_payload(payload)
