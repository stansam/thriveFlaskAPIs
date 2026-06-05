from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, after_log, RetryError

from app.core.errors.handlers import BadRequestError, KayakAPIError
from app.interface.adapter.base import AdapterBaseService
from app.core.logging import get_logger
from app.dto import FlightDetails

logger = get_logger(__name__)

_KAYAK_ALT_BASE_URL   = "https://kayak-api.p.rapidapi.com"
_ENDPOINT_DETAILS     = "/get-flight-details"
_DETAILS_CACHE_TTL    = 60     # 1 min

_SAFE_ID_RE   = re.compile(r'^[\w\-]{1,256}$')
_AIRLINE_RE   = re.compile(r'^[A-Z0-9]{2,3}$')
_FLIGHT_NO_RE = re.compile(r'^\d{1,4}$')


class KayakFlightDetailsAdapter(AdapterBaseService):
    def _validate_offer_id(self, offer_id: str) -> None:
        if not _SAFE_ID_RE.fullmatch(offer_id):
            raise BadRequestError(f"Invalid offer ID format: {offer_id!r}")

    def _validate_airline_code(self, airline_code: str) -> None:
        if not _AIRLINE_RE.fullmatch(airline_code):
            raise BadRequestError(f"Invalid airline code format: {airline_code!r}")

    def _validate_flight_number(self, flight_number: str) -> None:
        if not _FLIGHT_NO_RE.fullmatch(flight_number):
            raise BadRequestError(f"Invalid flight number format: {flight_number!r}")

    def get_flight_details(
        self,
        airline_code: str,
        flight_number: str,
        departure_date: date,
    ) -> list[FlightDetails]:
        """
        Get real-time details/status for a flight.
        """
        airline_code = airline_code.strip().upper()
        self._validate_airline_code(airline_code)

        flight_number = flight_number.strip()
        self._validate_flight_number(flight_number)

        if not isinstance(departure_date, date):
            raise BadRequestError("Departure date must be a date object.")

        cache_key = self._cache_key(
            "flight_details",
            airline_code,
            flight_number,
            departure_date.isoformat(),
        )

        cached = self._cache_get_details(cache_key)
        if cached is not None:
            logger.info("Flight details cache HIT: %s", cache_key[-8:])
            return cached
        logger.info("Flight details cache MISS: %s", cache_key[-8:])

        params = {
            "departure_date": departure_date.isoformat(),
            "flight_number": flight_number,
            "airline_id": airline_code,
        }

        try:
            raw = self._call_flight_details(params)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:300]
            logger.error("Kayak Flight Details API HTTP %d: %s", status, body)
            raise KayakAPIError(message=f"Flight details API error (HTTP {status}).")
        except httpx.TimeoutException:
            raise KayakAPIError(message="Flight details request timed out.")
        except httpx.RequestError as exc:
            raise KayakAPIError(message=f"Flight details network error: {exc}")
        except RetryError:
            raise KayakAPIError(message="Flight details search failed after 3 attempts.")

        results = self._parse_flight_details_response(raw)
        self._cache_set_details(cache_key, results)
        return results

    def _parse_flight_details_response(self, raw: dict[str, Any]) -> list[FlightDetails]:
        results = []
        data = raw.get("data", {})
        flights = data.get("flights", []) if isinstance(data, dict) else []
        for item in flights:
            try:
                flight_no = str(item.get("flightNumberString") or item.get("flightNumber") or "")
                results.append(FlightDetails(
                    flight_number=flight_no,
                    airline_code=item.get("airlineCode", ""),
                    airline_name=item.get("airlineDispName", ""),
                    origin=item.get("departureAirport", ""),
                    destination=item.get("arrivalAirport", ""),
                    departure_scheduled=int(item.get("departureGateScheduled") or 0),
                    arrival_scheduled=int(item.get("arrivalGateScheduled") or 0),
                    departure_delay_min=int(item.get("departureDelay") or 0),
                    arrival_delay_min=int(item.get("arrivalDelay") or 0),
                    duration_min=int(item.get("flightDuration") or 0),
                    status_code=item.get("statusCode", ""),
                    aircraft_type=item.get("aircraftTypeName", ""),
                    latitude=float(item.get("latitude")) if item.get("latitude") is not None else None,
                    longitude=float(item.get("longitude")) if item.get("longitude") is not None else None,
                ))
            except Exception as exc:
                logger.warning("Failed to parse flight details item: %s", exc)
        return results

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        after=after_log(logger, logging.WARNING),
    )
    def _call_flight_details(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self._guard_api_key():
            return self._mock_flight_details_response(params)

        headers = self._request_headers()
        headers["X-RapidAPI-Host"] = "kayak-api.p.rapidapi.com"

        resp = httpx.get(
            f"{_KAYAK_ALT_BASE_URL}{_ENDPOINT_DETAILS}",
            headers=headers,
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()

    def _cache_get_details(self, key: str) -> list[FlightDetails] | None:
        if not self._redis:
            return None
        try:
            val = self._redis.get(key)
            if not val:
                return None
            data = json.loads(val)
            return [FlightDetails(**item) for item in data]
        except Exception as exc:
            logger.warning("Flight details cache read failed: %s", exc)
            return None

    def _cache_set_details(self, key: str, results: list[FlightDetails]) -> None:
        if not self._redis:
            return
        try:
            data = [
                {
                    "flight_number": r.flight_number,
                    "airline_code": r.airline_code,
                    "airline_name": r.airline_name,
                    "origin": r.origin,
                    "destination": r.destination,
                    "departure_scheduled": r.departure_scheduled,
                    "arrival_scheduled": r.arrival_scheduled,
                    "departure_delay_min": r.departure_delay_min,
                    "arrival_delay_min": r.arrival_delay_min,
                    "duration_min": r.duration_min,
                    "status_code": r.status_code,
                    "aircraft_type": r.aircraft_type,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                }
                for r in results
            ]
            self._redis.set(key, json.dumps(data), ex=_DETAILS_CACHE_TTL)
        except Exception as exc:
            logger.warning("Flight details cache write failed: %s", exc)

    def _mock_flight_details_response(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "error": None,
            "data": {
                "error": False,
                "flights": [
                    {
                        "aircraftTypeName": "Airbus A321neo",
                        "airlineCode": params.get("airline_id", "NK"),
                        "airlineDispName": "Spirit Airlines",
                        "airlineLogoURL": "/rimg/provider-logos/airlines/v/NK.png",
                        "altitude": 25,
                        "arrivalAirport": "EWR",
                        "arrivalAirportCity": "Newark",
                        "arrivalAirportCountry": "US",
                        "arrivalAirportName": "Newark",
                        "arrivalAirportState": "NJ",
                        "arrivalCity": "Newark",
                        "arrivalDelay": -35,
                        "arrivalGateDelay": -35,
                        "arrivalRunwayDelay": -31,
                        "arrivalTerminal": "B",
                        "arrivalGateScheduled": 1771364100000,
                        "departureAirport": "LAX",
                        "departureAirportCity": "Los Angeles",
                        "departureAirportCountry": "US",
                        "departureAirportName": "Los Angeles",
                        "departureAirportState": "CA",
                        "departureCity": "Los Angeles",
                        "departureDelay": 3,
                        "departureGateDelay": 3,
                        "departureGateScheduled": 1771345200000,
                        "flightDuration": 277,
                        "flightHistoryId": 1367430818,
                        "flightNumber": int(params.get("flight_number") or 1693),
                        "flightNumberString": str(params.get("flight_number") or "1693"),
                        "latitude": 40.7032,
                        "longitude": -74.15796,
                        "speed": 143,
                        "statusCode": "L",
                    }
                ],
                "query_info": {
                    "airline_code": params.get("airline_id", "NK"),
                    "date": params.get("departure_date", "2026-02-17"),
                    "flight_number": str(params.get("flight_number") or "1693"),
                },
                "total_flights": 1,
            },
        }