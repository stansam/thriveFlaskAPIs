import pytest
from app.models.client import Client
from app.enums import ClientType

def test_client_creation(db_session):
    """Test Client model creation and defaults."""
    client = Client(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    assert client.id is not None
    assert client.full_name == "Alice Smith"
    assert client.is_active is True
    assert client.preferred_language == "en"
