from datetime import datetime

class ResponseMapper:
    def normalize_search_response(self, raw_response: dict) -> list[dict]:
        """
        Transforms the raw Kayak-style JSON response into a normalized list of itineraries.
        """
        # 1. Extract Lookup Tables
        airlines = {a['code']: a['name'] for a in raw_response.get('airlines', [])}
        airports = {a['code']: a['name'] for a in raw_response.get('airports', [])}
        
        # Legs and Segments are keyed by ID (e.g., "L1", "S1")
        raw_legs = {l['id']: l for l in raw_response.get('legs', [])}
        raw_segments = {s['id']: s for s in raw_response.get('segments', [])}
        
        normalized_results = []
        
        for result in raw_response.get('results', []):
            # Skip if not a flight result (sometimes ads are mixed in)
            if 'legs' not in result or not result.get('bookingOptions'):
                continue

            # Identify the lowest price option
            best_option = min(result['bookingOptions'], key=lambda x: x['totalPrice'])
            
            itinerary = {
                "id": result['resultId'],  # Use resultId as unique identifier
                "price": {
                    "amount": best_option['totalPrice'],
                    "currency": "USD" # Assuming USD default, API might return strict currency
                },
                "legs": [],
                "booking_token": best_option['bookingUrl'] # Deep link or token
            }
            
            # Process each leg of the journey (Outbound, Return)
            for leg_ref in result['legs']:
                leg_id = leg_ref['id']
                raw_leg = raw_legs.get(leg_id)
                if not raw_leg:
                    continue
                
                normalized_leg = {
                    "departure": {
                        "airport": raw_leg['departureAirportCode'],
                        "time": raw_leg['departureTime']
                    },
                    "arrival": {
                        "airport": raw_leg['arrivalAirportCode'],
                        "time": raw_leg['arrivalTime']
                    },
                    "duration_mins": raw_leg['duration'],
                    "stops": raw_leg['stopCount'],
                    "segments": []
                }
                
                # Process segments within the leg
                for segment_ref in raw_leg.get('segments', []):
                    seg_id = segment_ref['id']
                    raw_seg = raw_segments.get(seg_id)
                    if not raw_seg:
                        continue
                        
                    airline_code = raw_seg['airlineCode']
                    normalized_leg['segments'].append({
                        "carrier": {
                            "code": airline_code,
                            "name": airlines.get(airline_code, airline_code),
                            "logo": f"https://content.r9cdn.net{raw_seg.get('airlineLogoUrl', '')}" if raw_seg.get('airlineLogoUrl') else None
                        },
                        "flight_number": raw_seg['flightNumber'],
                        "departure": {
                            "airport": raw_seg['departureAirportCode'],
                            "time": raw_seg['departureTime']
                        },
                        "arrival": {
                            "airport": raw_seg['arrivalAirportCode'],
                            "time": raw_seg['arrivalTime']
                        },
                        "duration_mins": raw_seg['duration']
                    })
                
                itinerary['legs'].append(normalized_leg)
            
            normalized_results.append(itinerary)
            
        return normalized_results
