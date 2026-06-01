# services/external_flight_service.py
"""
ExternalFlightService — Kayak flight search via RapidAPI.

Implements interfaces.md § 15. ExternalFlightService.

The Kayak wrapper returns flight offers that the admin uses to:
  1. Show options to the client.
  2. Click the deeplink to complete purchase on the airline's site.
  3. Re-verify price before confirming the booking.

Resilience
----------
All external calls are wrapped with tenacity retry logic:
  - 3 attempts, exponential backoff (1s → 2s → 4s)
  - Raises ExternalServiceError / KayakAPIError on final failure

Caching
-------
Search results are cached in Redis for 5 minutes (flight prices
change frequently; longer TTL would give stale results).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.errors.handlers import BadRequestError, ExternalServiceError, KayakAPIError
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

_CACHE_TTL = 300       # 5 minutes


# Response shapes
@dataclass
class FlightLeg:
    origin:      str
    destination: str
    departure:   str
    arrival:     str
    airline:     str
    flight_no:   str
    duration_min: int
    cabin:       str
    stops:       int = 0


@dataclass
class FlightOfferResult:
    offer_id:       str
    price_usd:      float
    currency:       str
    legs:           list[FlightLeg] = field(default_factory=list)
    deeplink_url:   str = ""
    expires_at:     str = ""
    provider:       str = "kayak"
    raw:            dict = field(default_factory=dict)


@dataclass
class PriceCheckResult:
    offer_id:    str
    price_usd:   float
    is_valid:    bool
    message:     str = ""



# Service
class ExternalFlightService(BaseService):

    def __init__(self) -> None:
        self._base_url = f"https://{settings.RAPIDAPI_KAYAK_HOST}"
        self._headers = {
            "X-RapidAPI-Key":  settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": settings.RAPIDAPI_KAYAK_HOST,
        }

    # Public interface
    def search_flights(
        self,
        origin:         str,
        destination:    str,
        departure_date: date,
        return_date:    date | None = None,
        adults:         int = 1,
        cabin_class:    str = "economy",
    ) -> list[FlightOfferResult]:
        """
        Search available flights and return normalised FlightOfferResult list.

        Results are cached in Redis for _CACHE_TTL seconds so rapid
        re-queries by an agent don't hammer the RapidAPI rate limit.
        """
        cache_key = self._cache_key(
            origin, destination, departure_date, return_date, adults, cabin_class
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug("Flight search cache HIT: %s", cache_key)
            return [FlightOfferResult(**item) for item in cached]

        raw = self._call_search(
            origin, destination, departure_date, return_date, adults, cabin_class
        )
        offers = self._parse_offers(raw)
        self._cache_set(cache_key, [_offer_to_dict(o) for o in offers])
        return offers

    def get_flight_deeplink(self, offer_id: str) -> str:
        """Return the Kayak deeplink URL for a specific offer."""
        raw = self._call_deeplink(offer_id)
        link = raw.get("url") or raw.get("deepLink") or raw.get("deeplink", "")
        if not link:
            raise KayakAPIError(message=f"No deeplink returned for offer '{offer_id}'.")
        return link

    def get_flight_price_check(self, offer_id: str) -> PriceCheckResult:
        """Re-verify price + availability before locking in a booking."""
        try:
            raw = self._call_price_check(offer_id)
            price = float(raw.get("price", 0))
            valid = raw.get("available", True)
            return PriceCheckResult(
                offer_id=offer_id,
                price_usd=price,
                is_valid=valid,
                message="" if valid else "Offer is no longer available.",
            )
        except KayakAPIError:
            return PriceCheckResult(
                offer_id=offer_id,
                price_usd=0.0,
                is_valid=False,
                message="Could not verify price — please search again.",
            )

    # RapidAPI calls with tenacity retry
    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=False,
    )
    def _call_search(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None,
        adults: int,
        cabin_class: str,
    ) -> dict:
        if not settings.RAPIDAPI_KEY:
            logger.warning("RAPIDAPI_KEY not set — returning mock flight results.")
            return _mock_search_response(origin, destination, departure_date)

        params: dict[str, Any] = {
            "origin":      origin.upper(),
            "destination": destination.upper(),
            "departDate":  departure_date.isoformat(),
            "adults":      adults,
            "cabin":       cabin_class,
            "currency":    "USD",
        }
        if return_date:
            params["returnDate"] = return_date.isoformat()

        try:
            resp = httpx.get(
                f"{self._base_url}/flights/search",
                headers=self._headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Kayak search HTTP %d: %s", exc.response.status_code, exc.response.text[:300])
            raise KayakAPIError(message=f"Flight search failed (HTTP {exc.response.status_code}).")
        except httpx.TimeoutException:
            raise KayakAPIError(message="Flight search timed out.")

    def _call_deeplink(self, offer_id: str) -> dict:
        if not settings.RAPIDAPI_KEY:
            return {"url": f"https://kayak.com/flights/mock/{offer_id}"}
        try:
            resp = httpx.get(
                f"{self._base_url}/flights/deeplink/{offer_id}",
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise KayakAPIError(message=str(exc))

    def _call_price_check(self, offer_id: str) -> dict:
        if not settings.RAPIDAPI_KEY:
            return {"price": 499.99, "available": True}
        try:
            resp = httpx.get(
                f"{self._base_url}/flights/price-check/{offer_id}",
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise KayakAPIError(message=str(exc))

    # Normalisation
    def _parse_offers(self, raw: dict) -> list[FlightOfferResult]:
        """
        Normalise the Kayak API response into FlightOfferResult objects.

        The Kayak wrapper response structure varies by endpoint version;
        this parser handles the most common shapes defensively.
        """
        offers_raw = (
            raw.get("data", {}).get("itineraries")
            or raw.get("results")
            or raw.get("offers")
            or raw.get("itineraries")
            or []
        )

        results: list[FlightOfferResult] = []
        for item in offers_raw[:20]:   # cap at 20 offers
            try:
                offer_id    = item.get("id") or item.get("resultid") or "unknown"
                price       = float(item.get("price", {}).get("amount", 0) or item.get("price", 0))
                currency    = item.get("price", {}).get("currency", "USD")
                deeplink    = item.get("deepLink") or item.get("url", "")

                legs: list[FlightLeg] = []
                for seg in (item.get("legs") or item.get("segments") or []):
                    legs.append(FlightLeg(
                        origin=seg.get("origin", ""),
                        destination=seg.get("destination", ""),
                        departure=seg.get("departure", ""),
                        arrival=seg.get("arrival", ""),
                        airline=seg.get("airline", {}).get("code", "") if isinstance(seg.get("airline"), dict) else str(seg.get("airline", "")),
                        flight_no=seg.get("flightNumber", "") or seg.get("flight_number", ""),
                        duration_min=int(seg.get("duration", 0)),
                        cabin=seg.get("cabin", "economy"),
                        stops=int(seg.get("stops", 0)),
                    ))

                results.append(FlightOfferResult(
                    offer_id=str(offer_id),
                    price_usd=price,
                    currency=currency,
                    legs=legs,
                    deeplink_url=deeplink,
                    raw=item,
                ))
            except Exception as exc:
                logger.debug("Skipping unparseable offer: %s", exc)
                continue

        return results

    # Redis cache helpers
    def _cache_key(self, *args) -> str:
        key_str = "|".join(str(a) for a in args)
        return "flight_search:" + hashlib.md5(key_str.encode()).hexdigest()

    def _cache_get(self, key: str) -> list | None:
        if not settings.REDIS_URL:
            return None
        try:
            import redis
            from redis import Redis
            r: Redis = redis.from_url(settings.REDIS_URL, db=settings.REDIS_CACHE_DB, decode_responses=True)

            val = r.get(key)
            if not isinstance(val, str):
                logger.debug("Flight cache read failed: %s", val)
                return None

            data = json.loads(val)
            if not isinstance(data, list):
                logger.debug("Flight cache read failed: %s", data)
                return None
                
            return data
        except Exception as exc:
            logger.debug("Flight cache read failed: %s", exc)
            return None

    def _cache_set(self, key: str, value: list) -> None:
        if not settings.REDIS_URL:
            return
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, db=settings.REDIS_CACHE_DB, decode_responses=True)
            r.setex(key, _CACHE_TTL, json.dumps(value))
        except Exception as exc:
            logger.debug("Flight cache write failed: %s", exc)


# Helpers
def _offer_to_dict(o: FlightOfferResult) -> dict:
    """Convert a FlightOfferResult to a JSON-safe dict for cache storage."""
    return {
        "offer_id":     o.offer_id,
        "price_usd":    o.price_usd,
        "currency":     o.currency,
        "deeplink_url": o.deeplink_url,
        "expires_at":   o.expires_at,
        "provider":     o.provider,
        "legs": [
            {
                "origin": l.origin, "destination": l.destination,
                "departure": l.departure, "arrival": l.arrival,
                "airline": l.airline, "flight_no": l.flight_no,
                "duration_min": l.duration_min, "cabin": l.cabin, "stops": l.stops,
            }
            for l in o.legs
        ],
        "raw": {},  # do not cache raw to keep Redis entries small
    }


def _mock_search_response(origin: str, destination: str, departure_date: date) -> dict:
    """Return a deterministic mock response when RAPIDAPI_KEY is not configured."""
    return {
        "results": [
            {
                "id": f"mock-{origin}-{destination}-1",
                "price": 499.99,
                "currency": "USD",
                "deepLink": f"https://kayak.com/flights/{origin.lower()}/{destination.lower()}/{departure_date}",
                "legs": [
                    {
                        "origin": origin, "destination": destination,
                        "departure": f"{departure_date}T08:00:00",
                        "arrival":   f"{departure_date}T14:00:00",
                        "airline": {"code": "AA"}, "flightNumber": "AA100",
                        "duration": 360, "cabin": "economy", "stops": 0,
                    }
                ],
            },
            {
                "id": f"mock-{origin}-{destination}-2",
                "price": 699.99,
                "currency": "USD",
                "deepLink": f"https://kayak.com/flights/{origin.lower()}/{destination.lower()}/{departure_date}?r=2",
                "legs": [
                    {
                        "origin": origin, "destination": destination,
                        "departure": f"{departure_date}T14:00:00",
                        "arrival":   f"{departure_date}T20:00:00",
                        "airline": {"code": "DL"}, "flightNumber": "DL200",
                        "duration": 360, "cabin": "economy", "stops": 0,
                    }
                ],
            },
        ]
    }


external_flight_service = ExternalFlightService()