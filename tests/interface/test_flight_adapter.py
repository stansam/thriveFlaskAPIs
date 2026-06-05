# tests/interface/test_flight_adapter.py
"""
Unit tests for ExternalFlightService and flight types.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
import pytest

from app.core.errors.handlers import BadRequestError, ExternalServiceError
from app.interface.adapter import adapter
from app.enums import PassengerType
from app.dto import (
    FlightSearchRequest, FlightSearchResponse, FlightOfferResult, 
    FlightLegDetail, FlightSegment, BookingOption, 
)


def test_flight_search_request_validation():
    # Valid request
    req = FlightSearchRequest(
        origin="LAX",
        destination="JFK",
        departure_date=date.today() + timedelta(days=1),
        return_date=date.today() + timedelta(days=5),
        passengers=[PassengerType.ADT],
    )
    assert req.origin == "LAX"
    assert req.destination == "JFK"

    # Normalize lowercase origin/destination
    req2 = FlightSearchRequest(
        origin="lax",
        destination="jfk",
        departure_date=date.today() + timedelta(days=1),
    )
    assert req2.origin == "LAX"
    assert req2.destination == "JFK"

    # Invalid origin
    with pytest.raises(BadRequestError, match="Origin must be a 2-4 letter IATA code"):
        FlightSearchRequest(
            origin="L",
            destination="JFK",
            departure_date=date.today() + timedelta(days=1),
        )

    # Invalid destination
    with pytest.raises(BadRequestError, match="Destination must be a 2-4 letter IATA code"):
        FlightSearchRequest(
            origin="LAX",
            destination="JFK1",
            departure_date=date.today() + timedelta(days=1),
        )

    # Past date
    with pytest.raises(BadRequestError, match="cannot be in the past"):
        FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date.today() - timedelta(days=1),
        )

    # Return date before departure date
    with pytest.raises(BadRequestError, match="cannot be before departure date"):
        FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date.today() + timedelta(days=5),
            return_date=date.today() + timedelta(days=1),
        )

    # Empty passengers
    with pytest.raises(BadRequestError, match="Passengers list cannot be empty"):
        FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date.today() + timedelta(days=1),
            passengers=[],
        )

    # Invalid passenger type
    with pytest.raises(BadRequestError, match="Invalid passenger type"):
        FlightSearchRequest(
            origin="LAX",
            destination="JFK",
            departure_date=date.today() + timedelta(days=1),
            passengers=["INVALID"],  # type: ignore
        )


def test_parse_search_response(app):
    # Load JSON fixture
    fixture_path = os.path.join(os.path.dirname(app.root_path), "externalJSON", "xeFlightSearchResp.json")
    with open(fixture_path) as f:
        raw = json.load(f)

    response = adapter.flight_search._parse_search_response(raw)

    assert isinstance(response, FlightSearchResponse)
    assert response.search_id == "qjEiM3iB83"
    assert response.page_number == 2
    assert response.page_size == 15
    assert response.total_count == 1399
    assert response.filtered_count == 1024
    assert response.regular_flights == 19
    assert len(response.results) > 0

    # Test the first core result (excluding ad)
    first_result = response.results[0]
    assert first_result.result_id == "4208d20a291ecb3a4789ce4a1ade4e28"
    assert len(first_result.legs) == 2
    assert first_result.is_best is False
    assert first_result.is_cheapest is False

    # Test legs and segments
    leg = first_result.legs[0]
    assert leg.leg_id == "LAXMCO1771621200000NK9861771660800000NK7002"
    assert len(leg.segments) == 2

    segment = leg.segments[0]
    assert segment.segment_id == "1771621200000NK9861631"
    assert segment.origin == "LAX"
    assert segment.destination == "DTW"
    assert segment.airline_code == "NK"
    assert segment.flight_number == "986"
    assert segment.duration_min == 263
    assert segment.equipment_type == "Airbus A321neo"
    assert segment.cabin_code == "e"
    assert segment.cabin_display == "Economy"

    # Test booking options
    assert len(first_result.booking_options) > 0
    bo = first_result.booking_options[0]
    assert bo.provider_code == "CHEAPFLIGHTSFARES"
    assert bo.price_per_person == 353.0
    assert bo.total_price == 1765.0
    assert bo.currency == "USD"
    assert bo.carry_on_status == "FEE"
    assert bo.checked_bag_status == "FEE"
    assert bo.booking_url.startswith("https://www.kayak.com/book/flight?code=")


def test_parse_flight_details(app):
    fixture_path = os.path.join(os.path.dirname(app.root_path), "externalJSON", "xeFlightDetailsResp.json")
    with open(fixture_path) as f:
        raw = json.load(f)

    details_list = adapter.flight_details._parse_flight_details_response(raw)

    assert len(details_list) == 1
    details = details_list[0]
    assert details.flight_number == "1693"
    assert details.airline_code == "NK"
    assert details.airline_name == "Spirit Airlines"
    assert details.origin == "LAX"
    assert details.destination == "EWR"
    assert details.departure_scheduled == 1771345200000
    assert details.arrival_scheduled == 1771364100000
    assert details.departure_delay_min == 3
    assert details.arrival_delay_min == -35
    assert details.duration_min == 277
    assert details.status_code == "L"
    assert details.aircraft_type == "Airbus A321neo"
    assert details.latitude == 40.7032
    assert details.longitude == -74.15796


def test_response_hydration():
    # Construct a complete nested FlightSearchResponse object
    segment = FlightSegment(
        segment_id="seg-123",
        origin="LAX",
        destination="JFK",
        departure="2026-02-20T08:00:00",
        arrival="2026-02-20T14:00:00",
        airline_code="AA",
        flight_number="100",
        duration_min=360,
        equipment_type="Boeing 777",
        cabin_code="b",
        cabin_display="Business",
    )
    leg = FlightLegDetail(
        leg_id="leg-123",
        departure="2026-02-20T08:00:00",
        arrival="2026-02-20T14:00:00",
        duration_min=360,
        segments=[segment],
    )
    bo = BookingOption(
        booking_id="bo-123",
        provider_code="AA",
        booking_url="https://www.kayak.com/book/123",
        price_per_person=500.0,
        total_price=500.0,
        currency="USD",
        carry_on_status="INCLUDED",
        checked_bag_status="INCLUDED",
    )
    offer = FlightOfferResult(
        result_id="result-123",
        trip_id="trip-123",
        is_best=True,
        is_cheapest=False,
        legs=[leg],
        booking_options=[bo],
        total_booking_options=1,
        shareable_url="https://www.kayak.com/share",
    )
    original_response = FlightSearchResponse(
        search_id="search-123",
        page_number=1,
        page_size=15,
        total_count=1,
        filtered_count=1,
        sort_mode="bestflight_a",
        price_mode="per-person",
        status="complete",
        results=[offer],
        regular_flights=1,
    )

    serialized = adapter.flight_search._response_to_dict(original_response)
    hydrated = adapter.flight_search._hydrate_response(serialized)

    assert hydrated == original_response


def test_mock_search_flow(monkeypatch):
    # Force mock mode by setting RAPIDAPI_KEY to empty string
    from app.core.config import settings
    monkeypatch.setattr(settings, "RAPIDAPI_KEY", "")

    # Make a FlightSearchRequest
    request = FlightSearchRequest(
        origin="LAX",
        destination="JFK",
        departure_date=date.today() + timedelta(days=2),
    )

    response = adapter.flight_search.search_flights(request)

    assert isinstance(response, FlightSearchResponse)
    assert response.search_id == "mock-search-id-123"
    assert len(response.results) == 2
    assert response.results[0].result_id == "mock-result-LAX-JFK-1"
