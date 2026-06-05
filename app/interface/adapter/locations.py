from __future__ import annotations

import json
import logging
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, after_log, RetryError
from app.core.errors.handlers import BadRequestError, KayakAPIError
from app.core.logging import get_logger
from app.dto import LocationResult
from app.interface.adapter.base import AdapterBaseService

logger = get_logger(__name__)

_LOCATION_CACHE_TTL   = 3600   # 1 hour
_ENDPOINT_LOCATIONS   = "/search-locations"

class KayakLocationsAdapter(AdapterBaseService):
    
    def search_locations(
        self,
        query: str,
        location_type: str = "airportonly",
        locale: str = "en",
        country: str = "US",
    ) -> list[LocationResult]:
        """
        Search for locations (airports, cities, or all) matching query.
        """
        query = query.strip()
        if not query:
            raise BadRequestError("Query parameter cannot be empty.")
        if len(query) > 100:
            raise BadRequestError("Query parameter is too long.")

        location_type = location_type.strip().lower()
        if location_type not in ("airportonly", "cityonly", "all"):
            raise BadRequestError(
                f"Invalid location_type: {location_type!r}. Must be 'airportonly', 'cityonly', or 'all'."
            )

        cache_key = self._cache_key(
            "location_search",
            query.lower(),
            location_type,
            locale,
            country,
        )

        cached = self._cache_get_locations(cache_key)
        if cached is not None:
            logger.info("Location search cache HIT: %s", cache_key[-8:])
            return cached
        logger.info("Location search cache MISS: %s", cache_key[-8:])

        params = {
            "query": query,
            "type": location_type,
            "locale": locale,
            "country": country,
        }

        try:
            raw = self._call_location(params)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:300]
            logger.error("Kayak Location API HTTP %d: %s", status, body)
            raise KayakAPIError(message=f"Location API error (HTTP {status}).")
        except httpx.TimeoutException:
            raise KayakAPIError(message="Location request timed out.")
        except httpx.RequestError as exc:
            raise KayakAPIError(message=f"Location network error: {exc}")
        except RetryError:
            raise KayakAPIError(message="Location search failed after 3 attempts.")

        results = self._parse_location_response(raw)
        self._cache_set_locations(cache_key, results)
        return results
    
    def _parse_location_response(self, raw: dict[str, Any]) -> list[LocationResult]:
        results = []
        data = raw.get("data", {})
        items = data.get("results", []) if isinstance(data, dict) else []
        for item in items:
            try:
                results.append(LocationResult(
                    id=item.get("id", ""),
                    airport_name=item.get("airportname", ""),
                    city_name=item.get("cityname", ""),
                    display_name=item.get("displayname", ""),
                    city=item.get("city", ""),
                    country=item.get("country", ""),
                    country_code=item.get("countrycode", ""),
                    lat=float(item.get("lat") or 0.0),
                    lng=float(item.get("lng") or 0.0),
                    timezone=item.get("timezone", ""),
                ))
            except Exception as exc:
                logger.warning("Failed to parse location item: %s", exc)
        return results

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        after=after_log(logger, logging.WARNING),
    )
    def _call_location(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self._guard_api_key():
            return self._mock_location_response(params)

        resp = httpx.get(
            f"{self._base_url}{_ENDPOINT_LOCATIONS}",
            headers=self._request_headers(),
            params=params,
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()
    
    def _mock_location_response(self, params: dict[str, Any]) -> dict[str, Any]:
        q = params.get("query", "")
        return {
            "success": True,
            "error": None,
            "data": {
                "query": q,
                "count": 1,
                "results": [
                    {
                        "id": q.upper()[:3] if len(q) >= 3 else "MIA",
                        "airportname": f"{q.capitalize()} Airport",
                        "cityname": f"{q.capitalize()}, State, Country",
                        "displayname": f"{q.capitalize()} ({q.upper()[:3] if len(q) >= 3 else 'MIA'} - Airport)",
                        "city": q.capitalize(),
                        "state": "State",
                        "country": "United States",
                        "countrycode": "US",
                        "lat": 25.79325,
                        "lng": -80.29056,
                        "timezone": "America/New_York",
                    }
                ],
            },
        }

    def _cache_get_locations(self, key: str) -> list[LocationResult] | None:
        if not self._redis:
            return None
        try:
            val = self._redis.get(key)
            if not val:
                return None
            data = json.loads(val)
            return [LocationResult(**item) for item in data]
        except Exception as exc:
            logger.warning("Locations cache read failed: %s", exc)
            return None
    
    def _cache_set_locations(self, key: str, results: list[LocationResult]) -> None:
        if not self._redis:
            return
        try:
            data = [
                {
                    "id": r.id,
                    "airport_name": r.airport_name,
                    "city_name": r.city_name,
                    "display_name": r.display_name,
                    "city": r.city,
                    "country": r.country,
                    "country_code": r.country_code,
                    "lat": r.lat,
                    "lng": r.lng,
                    "timezone": r.timezone,
                }
                for r in results
            ]
            self._redis.set(key, json.dumps(data), ex=_LOCATION_CACHE_TTL)
        except Exception as exc:
            logger.warning("Locations cache write failed: %s", exc)