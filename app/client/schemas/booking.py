from marshmallow import fields, validate, validates_schema, ValidationError
from app.schemas import BaseSchema
from app.models.enums import TravelClass

class FlightSegmentSchema(BaseSchema):
    carrier_code = fields.Str(required=True, validate=validate.Length(min=2, max=3))
    flight_number = fields.Str(required=True)
    departure_airport_code = fields.Str(required=True, validate=validate.Length(equal=3))
    arrival_airport_code = fields.Str(required=True, validate=validate.Length(equal=3))
    departure_time = fields.DateTime(required=True)
    arrival_time = fields.DateTime(required=True)
    duration_minutes = fields.Int(required=False, allow_none=True)
    aircraft_type = fields.Str(required=False, allow_none=True)
    baggage_allowance = fields.Str(required=False, allow_none=True)
    terminal = fields.Str(required=False, allow_none=True)
    gate = fields.Str(required=False, allow_none=True)

class FlightBookingSchema(BaseSchema):
    cabin_class = fields.Str(required=True, validate=validate.OneOf(TravelClass.list()))
    pnr_reference = fields.Str(required=False, allow_none=True)
    segments = fields.List(fields.Nested(FlightSegmentSchema), required=True, validate=validate.Length(min=1))

class PackageBookingSchema(BaseSchema):
    package_id = fields.Str(required=True, validate=validate.Length(equal=36))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    number_of_adults = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    number_of_children = fields.Int(required=False, load_default=0, validate=validate.Range(min=0))
    special_requests = fields.Str(required=False, allow_none=True)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise ValidationError("start_date cannot be after end_date")

class BulkPassengerItemSchema(BaseSchema):
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    date_of_birth = fields.Date(required=True)
    passport_number = fields.Str(required=False, allow_none=True)

class BookingPassengersSchema(BaseSchema):
    passengers = fields.List(fields.Nested(BulkPassengerItemSchema), required=True, validate=validate.Length(min=1))
