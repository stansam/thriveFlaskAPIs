from app.main import main_bp
from app.main.routes.flight import FlightSearch, FlightDetails, FlightBook

main_bp.add_url_rule('/api/flight/search', view_func=FlightSearch.as_view('flight_search'))
main_bp.add_url_rule('/api/flight/details/<flight_id>', view_func=FlightDetails.as_view('flight_details'))
main_bp.add_url_rule('/api/flight/book', view_func=FlightBook.as_view('flight_book'))