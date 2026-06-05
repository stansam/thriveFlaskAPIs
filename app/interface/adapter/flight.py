from __future__ import annotations

import json
import logging
import time
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, after_log, RetryError
from app.core.errors.handlers import BadRequestError, KayakAPIError
from app.interface.adapter.base import AdapterBaseService
from app.core.logging import get_logger
from app.enums import SortMode
from app.dto import (
    FlightSearchRequest, FlightSearchResponse, FlightOfferResult, 
    FlightLegDetail, FlightSegment, BookingOption, 
    PriceCheckResult
    )

logger = get_logger(__name__)

_ENDPOINT_SEARCH      = "/search-flights"
_BOOKING_BASE_URL     = "https://www.kayak.com"
_SEARCH_CACHE_TTL     = 300


class KayakFlightSearchAdapter(AdapterBaseService):

    def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """
        Search available flights and return a FlightSearchResponse.
        """
        if not isinstance(request, FlightSearchRequest):
            raise BadRequestError("Request must be a FlightSearchRequest object.")

        sorted_passengers = sorted(p.value for p in request.passengers)
        cache_key = self._cache_key(
            "flight_search",
            request.origin,
            request.destination,
            request.departure_date.isoformat(),
            request.return_date.isoformat() if request.return_date else "",
            tuple(sorted_passengers),
            request.filter_string,
            request.sort_mode.value,
            request.page_number,
        )

        cached = self._cache_get_search(cache_key)
        if cached is not None:
            logger.info("Flight search cache HIT: %s", cache_key[-8:])
            return cached
        logger.info("Flight search cache MISS: %s", cache_key[-8:])

        payload: dict[str, Any] = {
            "origin": request.origin,
            "destination": request.destination,
            "departure_date": request.departure_date.isoformat(),
        }
        if request.return_date:
            payload["return_date"] = request.return_date.isoformat()

        user_search: dict[str, Any] = {
            "passengers": [p.value for p in request.passengers],
        }
        if request.sort_mode != SortMode.BEST:
            user_search["sortMode"] = request.sort_mode.value
        payload["userSearchParams"] = user_search

        if request.filter_string:
            payload["filterParams"] = {"fs": request.filter_string}

        meta: dict[str, Any] = {}
        if request.page_number > 1:
            meta["pageNumber"] = request.page_number
        if request.search_id:
            meta["searchId"] = request.search_id
        if meta:
            payload["searchMetaData"] = meta

        start = time.perf_counter()
        try:
            raw = self._call_search(payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:300]
            logger.error("Kayak API HTTP %d: %s", status, body)
            raise KayakAPIError(message=f"API error (HTTP {status}).")
        except httpx.TimeoutException:
            raise KayakAPIError(message="Request timed out.")
        except httpx.RequestError as exc:
            raise KayakAPIError(message=f"Network error: {exc}")
        except RetryError:
            raise KayakAPIError(message="Flight search failed after 3 attempts.")

        response = self._parse_search_response(raw)

        logger.info(
            "Kayak flight search completed",
            extra={
                "origin": request.origin,
                "destination": request.destination,
                "departure_date": str(request.departure_date),
                "results_count": len(response.results),
                "total_count": response.total_count,
                "duration_ms": round(elapsed_ms),
                "cache_hit": False,
                "search_id": response.search_id,
            }
        )

        self._cache_set_search(cache_key, response)
        return response

    def get_booking_url(self, offer: FlightOfferResult) -> str:
        """Return the booking URL for the best offer option."""
        url = offer.best_booking_url
        if not url:
            raise KayakAPIError(message=f"No booking URL returned for offer '{offer.result_id}'.")
        return url

    def get_flight_price_check(self, offer: FlightOfferResult) -> PriceCheckResult:
        """Verify price and availability for a flight offer."""
        try:
            price = offer.best_price
            return PriceCheckResult(
                offer_id=offer.result_id,
                price_usd=price,
                is_valid=True,
                message="",
            )
        except Exception as exc:
            logger.warning("Price check failed for offer %s: %s", offer.result_id, exc)
            return PriceCheckResult(
                offer_id=offer.result_id,
                price_usd=0.0,
                is_valid=False,
                message="Could not verify price — please search again.",
            )

    def _hydrate_response(self, data: dict[str, Any]) -> FlightSearchResponse:
        results = []
        for r_data in data.get("results", []):
            legs = []
            for l_data in r_data.get("legs", []):
                segs = []
                for s_data in l_data.get("segments", []):
                    segs.append(FlightSegment(**s_data))
                legs.append(FlightLegDetail(
                    leg_id=l_data["leg_id"],
                    departure=l_data["departure"],
                    arrival=l_data["arrival"],
                    duration_min=l_data["duration_min"],
                    segments=segs,
                ))
            bos = []
            for bo_data in r_data.get("booking_options", []):
                bos.append(BookingOption(**bo_data))
            results.append(FlightOfferResult(
                result_id=r_data["result_id"],
                trip_id=r_data["trip_id"],
                is_best=r_data.get("is_best", False),
                is_cheapest=r_data.get("is_cheapest", False),
                legs=legs,
                booking_options=bos,
                total_booking_options=r_data.get("total_booking_options", 0),
                shareable_url=r_data.get("shareable_url", ""),
                provider=r_data.get("provider", "kayak"),
            ))
        return FlightSearchResponse(
            search_id=data["search_id"],
            page_number=data["page_number"],
            page_size=data["page_size"],
            total_count=data["total_count"],
            filtered_count=data["filtered_count"],
            sort_mode=data["sort_mode"],
            price_mode=data["price_mode"],
            status=data["status"],
            results=results,
            regular_flights=data.get("regular_flights", 0),
        )

    def _parse_search_response(self, raw: dict[str, Any]) -> FlightSearchResponse:
        data = raw.get("data", {})
        if not data:
            return FlightSearchResponse(
                search_id="",
                page_number=1,
                page_size=15,
                total_count=0,
                filtered_count=0,
                sort_mode="bestflight_a",
                price_mode="per-person",
                status="complete",
                results=[],
            )

        segments_dict = data.get("segments", {})
        legs_dict = data.get("legs", {})
        results_raw = data.get("results", [])

        parsed_results: list[FlightOfferResult] = []
        parse_failures = 0
        total_items = 0

        for result in results_raw:
            if result.get("type") == "inlineAd":
                continue
            total_items += 1
            try:
                result_legs = []
                for leg_ref in result.get("legs", []):
                    leg_id = leg_ref["id"]
                    leg_data = legs_dict.get(leg_id)
                    if not leg_data:
                        raise ValueError(f"Leg ID {leg_id} not found in global legs index")

                    cabin_map = {}
                    first_bo = result.get("bookingOptions", [{}])[0] if result.get("bookingOptions") else {}
                    for lf in first_bo.get("legFarings", []):
                        if lf.get("legId") == leg_id:
                            for sf in lf.get("segmentFarings", []):
                                seg_id = sf.get("segmentId")
                                if seg_id:
                                    cabin_map[seg_id] = (
                                        sf.get("cabinCode", "e"),
                                        sf.get("cabinDisplay", "Economy"),
                                    )

                    segments = []
                    for seg_ref in leg_data.get("segments", []):
                        seg_id = seg_ref["id"]
                        seg_data = segments_dict.get(seg_id)
                        if not seg_data:
                            raise ValueError(f"Segment ID {seg_id} not found in global segments index")

                        cabin_code, cabin_display = cabin_map.get(seg_id, ("e", "Economy"))
                        segments.append(FlightSegment(
                            segment_id=seg_id,
                            origin=seg_data.get("origin", ""),
                            destination=seg_data.get("destination", ""),
                            departure=seg_data.get("departure", ""),
                            arrival=seg_data.get("arrival", ""),
                            airline_code=seg_data.get("airline", ""),
                            flight_number=str(seg_data.get("flightNumber") or ""),
                            duration_min=int(seg_data.get("duration") or 0),
                            equipment_type=seg_data.get("equipmentTypeName", ""),
                            cabin_code=cabin_code,
                            cabin_display=cabin_display,
                        ))

                    result_legs.append(FlightLegDetail(
                        leg_id=leg_id,
                        departure=leg_data.get("departure", ""),
                        arrival=leg_data.get("arrival", ""),
                        duration_min=int(leg_data.get("duration") or 0),
                        segments=segments,
                    ))

                booking_options = []
                for bo in result.get("bookingOptions", []):
                    raw_url = bo.get("bookingUrl", {}).get("url", "")
                    url_type = bo.get("bookingUrl", {}).get("urlType", "relative")
                    if url_type == "relative":
                        abs_url = f"{_BOOKING_BASE_URL}{raw_url}"
                    else:
                        abs_url = raw_url

                    display_price = bo.get("displayPrice", {})
                    fees = bo.get("fees", {})
                    total = fees.get("totalPrice", {}).get("price", 0.0)

                    carry_on = fees.get("carryOnBagData", {}).get("status", "UNKNOWN")
                    checked = fees.get("checkedBagData", {}).get("status", "UNKNOWN")

                    booking_options.append(BookingOption(
                        booking_id=bo.get("bookingId", ""),
                        provider_code=bo.get("providerCode", ""),
                        booking_url=abs_url,
                        price_per_person=float(display_price.get("price") or 0.0),
                        total_price=float(total or 0.0),
                        currency=display_price.get("currency", "USD"),
                        carry_on_status=carry_on,
                        checked_bag_status=checked,
                    ))

                offer = FlightOfferResult(
                    result_id=result.get("resultId", ""),
                    trip_id=result.get("tripId", ""),
                    is_best=result.get("isBest", False),
                    is_cheapest=result.get("isCheapest", False),
                    legs=result_legs,
                    booking_options=booking_options,
                    total_booking_options=result.get("totalBookingOptions", 0),
                    shareable_url=result.get("shareableUrl", ""),
                )
                if not offer.result_id:
                    raise ValueError("Offer missing resultId")
                parsed_results.append(offer)
            except Exception as exc:
                parse_failures += 1
                logger.warning("Skipping unparseable offer: %s", exc)

        if total_items > 0:
            pct = parse_failures / total_items
            level = logging.ERROR if pct > 0.5 else logging.WARNING
            if parse_failures > 0:
                logger.log(level, "Offer parse failures: %d/%d (%.0f%%)", parse_failures, total_items, pct * 100)

        stats = data.get("result_statistics", {})
        regular_flights = int(stats.get("regular_flights") or len(parsed_results))

        return FlightSearchResponse(
            search_id=data.get("searchId", ""),
            page_number=int(data.get("pageNumber") or 1),
            page_size=int(data.get("pageSize") or 15),
            total_count=int(data.get("totalCount") or 0),
            filtered_count=int(data.get("filteredCount") or 0),
            sort_mode=data.get("sortMode", "bestflight_a"),
            price_mode=data.get("priceMode", "per-person"),
            status=data.get("status", "complete"),
            results=parsed_results,
            regular_flights=regular_flights,
        )

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
        after=after_log(logger, logging.WARNING),
    )
    def _call_search(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._guard_api_key():
            return self._mock_search_response(payload)

        resp = httpx.post(
            f"{self._base_url}{_ENDPOINT_SEARCH}",
            headers=self._request_headers(),
            json=payload,
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()
    
    def _hydrate_response(self, data: dict[str, Any]) -> FlightSearchResponse:
        results = []
        for r_data in data.get("results", []):
            legs = []
            for l_data in r_data.get("legs", []):
                segs = []
                for s_data in l_data.get("segments", []):
                    segs.append(FlightSegment(**s_data))
                legs.append(FlightLegDetail(
                    leg_id=l_data["leg_id"],
                    departure=l_data["departure"],
                    arrival=l_data["arrival"],
                    duration_min=l_data["duration_min"],
                    segments=segs,
                ))
            bos = []
            for bo_data in r_data.get("booking_options", []):
                bos.append(BookingOption(**bo_data))
            results.append(FlightOfferResult(
                result_id=r_data["result_id"],
                trip_id=r_data["trip_id"],
                is_best=r_data.get("is_best", False),
                is_cheapest=r_data.get("is_cheapest", False),
                legs=legs,
                booking_options=bos,
                total_booking_options=r_data.get("total_booking_options", 0),
                shareable_url=r_data.get("shareable_url", ""),
                provider=r_data.get("provider", "kayak"),
            ))
        return FlightSearchResponse(
            search_id=data["search_id"],
            page_number=data["page_number"],
            page_size=data["page_size"],
            total_count=data["total_count"],
            filtered_count=data["filtered_count"],
            sort_mode=data["sort_mode"],
            price_mode=data["price_mode"],
            status=data["status"],
            results=results,
            regular_flights=data.get("regular_flights", 0),
        )

    def _cache_get_search(self, key: str) -> FlightSearchResponse | None:
        if not self._redis:
            return None
        try:
            val = self._redis.get(key)
            if not val:
                return None
            data = json.loads(val)
            return self._hydrate_response(data)
        except Exception as exc:
            logger.warning("Flight cache read failed: %s", exc)
            return None
    
    def _cache_set_search(self, key: str, response: FlightSearchResponse) -> None:
        if not self._redis:
            return
        try:
            data = self._response_to_dict(response)
            self._redis.set(key, json.dumps(data), ex=_SEARCH_CACHE_TTL)
        except Exception as exc:
            logger.warning("Flight cache write failed: %s", exc)

    def _mock_search_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        origin = payload.get("origin", "LAX")
        destination = payload.get("destination", "JFK")
        dep_date = payload.get("departure_date", "2026-02-20")

        seg1 = f"mock-seg-{origin}-{destination}-1"
        seg2 = f"mock-seg-{origin}-{destination}-2"
        leg1 = f"mock-leg-{origin}-{destination}-1"
        leg2 = f"mock-leg-{origin}-{destination}-2"

        return {
            "success": True,
            "error": None,
            "data": {
                "searchId": "mock-search-id-123",
                "pageNumber": 1,
                "pageSize": 15,
                "totalCount": 2,
                "filteredCount": 2,
                "sortMode": "bestflight_a",
                "priceMode": "per-person",
                "status": "complete",
                "segments": {
                    seg1: {
                        "airline": "AA",
                        "arrival": f"{dep_date}T14:00:00",
                        "departure": f"{dep_date}T08:00:00",
                        "destination": destination,
                        "duration": 360,
                        "equipmentTypeName": "Boeing 777",
                        "flightNumber": "100",
                        "origin": origin,
                    },
                    seg2: {
                        "airline": "DL",
                        "arrival": f"{dep_date}T20:00:00",
                        "departure": f"{dep_date}T14:00:00",
                        "destination": destination,
                        "duration": 360,
                        "equipmentTypeName": "Airbus A350",
                        "flightNumber": "200",
                        "origin": origin,
                    },
                },
                "legs": {
                    leg1: {
                        "arrival": f"{dep_date}T14:00:00",
                        "departure": f"{dep_date}T08:00:00",
                        "duration": 360,
                        "segments": [{"id": seg1}],
                    },
                    leg2: {
                        "arrival": f"{dep_date}T20:00:00",
                        "departure": f"{dep_date}T14:00:00",
                        "duration": 360,
                        "segments": [{"id": seg2}],
                    },
                },
                "results": [
                    {
                        "type": "core",
                        "resultId": f"mock-result-{origin}-{destination}-1",
                        "tripId": f"mock-result-{origin}-{destination}-1",
                        "isBest": True,
                        "isCheapest": True,
                        "legs": [{"id": leg1}],
                        "bookingOptions": [
                            {
                                "bookingId": f"mock-booking-{origin}-{destination}-1",
                                "providerCode": "AMERICAN_AIRLINES",
                                "bookingUrl": {
                                    "url": "/book/flight?code=mock-1",
                                    "urlType": "relative",
                                },
                                "displayPrice": {
                                    "price": 350.00,
                                    "currency": "USD",
                                },
                                "fees": {
                                    "totalPrice": {
                                        "price": 350.00,
                                    },
                                    "carryOnBagData": {"status": "INCLUDED"},
                                    "checkedBagData": {"status": "FEE"},
                                },
                                "legFarings": [
                                    {
                                        "legId": leg1,
                                        "segmentFarings": [
                                            {
                                                "segmentId": seg1,
                                                "cabinCode": "e",
                                                "cabinDisplay": "Economy",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "totalBookingOptions": 1,
                        "shareableUrl": f"https://www.kayak.com/flights/share/mock-1",
                    },
                    {
                        "type": "core",
                        "resultId": f"mock-result-{origin}-{destination}-2",
                        "tripId": f"mock-result-{origin}-{destination}-2",
                        "isBest": False,
                        "isCheapest": False,
                        "legs": [{"id": leg2}],
                        "bookingOptions": [
                            {
                                "bookingId": f"mock-booking-{origin}-{destination}-2",
                                "providerCode": "DELTA",
                                "bookingUrl": {
                                    "url": "/book/flight?code=mock-2",
                                    "urlType": "relative",
                                },
                                "displayPrice": {
                                    "price": 450.00,
                                    "currency": "USD",
                                },
                                "fees": {
                                    "totalPrice": {
                                        "price": 450.00,
                                    },
                                    "carryOnBagData": {"status": "INCLUDED"},
                                    "checkedBagData": {"status": "INCLUDED"},
                                },
                                "legFarings": [
                                    {
                                        "legId": leg2,
                                        "segmentFarings": [
                                            {
                                                "segmentId": seg2,
                                                "cabinCode": "e",
                                                "cabinDisplay": "Economy",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                        "totalBookingOptions": 1,
                        "shareableUrl": f"https://www.kayak.com/flights/share/mock-2",
                    },
                ],
                "result_statistics": {
                    "filtered_ads": 0,
                    "regular_flights": 2,
                    "total_raw_results": 2,
                },
            },
        }

    def _response_to_dict(self, res: FlightSearchResponse) -> dict[str, Any]:
        return {
            "search_id": res.search_id,
            "page_number": res.page_number,
            "page_size": res.page_size,
            "total_count": res.total_count,
            "filtered_count": res.filtered_count,
            "sort_mode": res.sort_mode,
            "price_mode": res.price_mode,
            "status": res.status,
            "regular_flights": res.regular_flights,
            "results": [
                {
                    "result_id": o.result_id,
                    "trip_id": o.trip_id,
                    "is_best": o.is_best,
                    "is_cheapest": o.is_cheapest,
                    "total_booking_options": o.total_booking_options,
                    "shareable_url": o.shareable_url,
                    "provider": o.provider,
                    "booking_options": [
                        {
                            "booking_id": bo.booking_id,
                            "provider_code": bo.provider_code,
                            "booking_url": bo.booking_url,
                            "price_per_person": bo.price_per_person,
                            "total_price": bo.total_price,
                            "currency": bo.currency,
                            "carry_on_status": bo.carry_on_status,
                            "checked_bag_status": bo.checked_bag_status,
                        }
                        for bo in o.booking_options
                    ],
                    "legs": [
                        {
                            "leg_id": l.leg_id,
                            "departure": l.departure,
                            "arrival": l.arrival,
                            "duration_min": l.duration_min,
                            "segments": [
                                {
                                    "segment_id": s.segment_id,
                                    "origin": s.origin,
                                    "destination": s.destination,
                                    "departure": s.departure,
                                    "arrival": s.arrival,
                                    "airline_code": s.airline_code,
                                    "flight_number": s.flight_number,
                                    "duration_min": s.duration_min,
                                    "equipment_type": s.equipment_type,
                                    "cabin_code": s.cabin_code,
                                    "cabin_display": s.cabin_display,
                                }
                                for s in l.segments
                            ],
                        }
                        for l in o.legs
                    ],
                }
                for o in res.results
            ]
        }
