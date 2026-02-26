import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.main.schemas.flights import FlightSearchSchema
from app.services.flight.service import FlightService
from app.dto.flight.schemas import SearchFlightDTO, PassengerQueryDTO
from app.utils.analytics import track_metric
from app.extensions import socketio

logger = logging.getLogger(__name__)

class FlightSearchView(MethodView):
    def get(self):
        schema = FlightSearchSchema()
        try:
             # Load from URL query bindings explicitly
             # Handle nested dicts natively mapping from URL structs if needed
             raw_args = request.args.to_dict()
             
             # Safely extract dictionary structured params natively depending on Frontend mapping
             pass_args = {
                 'adults': int(request.args.get('passengers[adults]', 1)),
                 'children': int(request.args.get('passengers[children]', 0)),
                 'infants': int(request.args.get('passengers[infants]', 0))
             }
             raw_args['passengers'] = pass_args
             
             data = schema.load(raw_args)
        except ValidationError as err:
             return jsonify(err.messages), 400

        flight_service = FlightService()
        
        # NOTE: Ideally `FlightService.search_flights()` maps to a strict internal DTO explicitly.
        # Assuming the updated refactored `FlightService` accepts `SearchFlightDTO`.
        
        pass_dto = PassengerQueryDTO(
             adults=data['passengers']['adults'],
             children=data['passengers']['children'],
             infants=data['passengers']['infants']
        )
        
        search_payload = SearchFlightDTO(
            origin=data['origin'],
            destination=data['destination'],
            departure_date=data['date'],
            return_date=data.get('return_date'),
            passengers=pass_dto,
            cabin_class=data['cabin_class'],
            currency=data['currency']
        )
        
        try:
            results = flight_service.search_flights(search_payload)
            track_metric("flight_search_performed", category="main")
            
            # Emit websocket hook logic indicating search footprint natively
            socketio.emit('flight_search_completed', {
                'origin': data['origin'], 
                'destination': data['destination']
            })
            
            return jsonify({
                 "results": results
            }), 200
            
        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400
        except Exception as e:
             logger.error(f"Flight search GDS integration failed explicitly: {e}")
             return jsonify({"error": "Failed contacting global flight distributors."}), 503
