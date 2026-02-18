from marshmallow import fields, validate, validates_schema, ValidationError
from app.schemas.base import BaseSchema
from app.models.enums import Gender

class PassengerDetailSchema(BaseSchema):
    first_name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    last_name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    dob = fields.Date(required=True)
    gender = fields.String(required=True, validate=validate.OneOf([g.value for g in Gender]))
    passport_number = fields.String(required=True, validate=validate.Length(min=6, max=20))
    passport_expiry = fields.Date(required=True)
    # email and phone might be optional for additional passengers, mandatory for primary? 
    # Let's keep them optional or rely on User profile.

class BookingInitiateSchema(BaseSchema):
    flight_id = fields.String(required=True) # Token or Flight ID from Search
    expected_price = fields.Float(required=True) # Price user saw
    currency = fields.String(load_default="USD")
    passengers = fields.List(fields.Nested(PassengerDetailSchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def validate_passport(self, data, **kwargs):
        passengers = data.get('passengers', [])
        # TODO: Add logic to check passport expiry > 6 months from travel date if travel date was available here.
        # Since travel date is in flight_id (token), we might need to defer this or decoding token here.
        pass
