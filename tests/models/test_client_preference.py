import pytest
from app.models.client_preference import ClientPreference
from app.models.client import Client
from app.enums import ClientType, PreferredChannel, DocumentFormat

def test_client_preference_creation(db_session):
    """Test ClientPreference 1:1 relationship and defaults."""
    client = Client(
        first_name="Pref",
        last_name="Tester",
        email="pref@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    pref = ClientPreference(
        client_id=client.id,
        preferred_channel=PreferredChannel.EMAIL,
        preferred_document_format=DocumentFormat.PDF
    )
    db_session.add(pref)
    db_session.commit()

    assert pref.id is not None
    assert pref.client_id == client.id
    assert pref.marketing_opt_in is True
    assert pref.travel_reminder_hours == 48
