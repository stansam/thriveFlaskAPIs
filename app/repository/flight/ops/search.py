from datetime import datetime, timedelta

class SearchFlights:
    def execute(self, origin: str, destination: str, date: str) -> list[dict]:
        # MOCK IMPLEMENTATION
        # In a real app, this would query an Amadeus/Sabre API or a local flight schedule DB
        
        mock_flights = [
            {
                "id": "mock_f1",
                "carrier_code": "AA",
                "flight_number": "101",
                "departure_airport": origin,
                "arrival_airport": destination,
                "departure_time": f"{date}T08:00:00",
                "arrival_time": f"{date}T11:00:00",
                "price": 250.00,
                "currency": "USD"
            },
             {
                "id": "mock_f2",
                "carrier_code": "UA",
                "flight_number": "450",
                "departure_airport": origin,
                "arrival_airport": destination,
                "departure_time": f"{date}T14:00:00",
                "arrival_time": f"{date}T17:30:00",
                "price": 290.50,
                "currency": "USD"
            }
        ]
        return mock_flights
