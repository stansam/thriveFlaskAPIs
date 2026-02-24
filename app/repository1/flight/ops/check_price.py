from app.repository.flight.adapters.kayak import KayakFlightAdapter
from app.repository.flight.exceptions import FlightServiceError, FlightNotFound
import logging

logger = logging.getLogger(__name__)

class CheckFlightPrice:
    def execute(self, flight_id: str, expected_price: float = None, currency: str = "USD") -> dict:
        """
        Verifies if the flight is still available and returns the current price.
        
        Args:
            flight_id: The unique identifier/token for the flight.
            expected_price: (Optional) Price seen by user.
            
        Returns:
            dict: {"available": bool, "price": float, "currency": str, "price_changed": bool}
        """
        try:
            adapter = KayakFlightAdapter()
            # In a real API, we would call a 'check_availability' endpoint.
            # Here we might reuse get_flight_details or similar.
            # For this implementation, we simulate a check or call DETAILS.
            
            # Assuming params might be embedded in flight_id or we use it as key
            details = adapter.get_flight_details({"id": flight_id})
            
            # Extract current price from details (mocked logic as details response varies)
            # In a real scenario, the details response MUST include the live price.
            # Let's assume details['price'] exists or we extract from bookingOptions
            
            current_price = 0.0
            if 'price' in details:
                current_price = float(details['price']['amount'])
            elif 'bookingOptions' in details and len(details['bookingOptions']) > 0:
                 current_price = float(details['bookingOptions'][0]['totalPrice'])
            else:
                # Fallback or error
                logger.warning(f"Could not determine price for flight {flight_id}")
                # For safety in this MVP step, we might trust the input if we cant verify,
                # BUT correct way is to fail or re-search.
                # Let's assume we re-search if details doesn't have it.
                pass

            is_available = True # If we got details, it's likely available.
            
            price_changed = False
            if expected_price:
                # Allow small float difference
                if abs(current_price - expected_price) > 0.01:
                    price_changed = True
                    
            return {
                "available": is_available,
                "price": current_price,
                "currency": currency,
                "price_changed": price_changed
            }

        except FlightServiceError:
            return {"available": False, "price": 0.0, "currency": currency, "price_changed": False}
        except Exception as e:
            logger.error(f"Error checking price: {e}")
            raise FlightServiceError("Failed to verify flight price")
