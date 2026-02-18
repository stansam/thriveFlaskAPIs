from marshmallow import fields, validate, pre_load, ValidationError, validates_schema
from app.schemas.base import BaseSchema
from datetime import date

class PassengerSchema(BaseSchema):
    adults = fields.Integer(required=True, validate=validate.Range(min=1, max=9))
    children = fields.Integer(load_default=0, validate=validate.Range(min=0, max=9))
    infants = fields.Integer(load_default=0, validate=validate.Range(min=0, max=9))

class FlightSearchSchema(BaseSchema):
    origin = fields.String(required=True, validate=validate.Length(equal=3))
    destination = fields.String(required=True, validate=validate.Length(equal=3))
    date = fields.Date(required=True)
    return_date = fields.Date(load_default=None)
    passengers = fields.Nested(PassengerSchema, load_default=lambda: {"adults": 1, "children": 0, "infants": 0})
    cabin_class = fields.String(load_default="economy", validate=validate.OneOf(["economy", "business", "first", "premium_economy"]))
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))

    @pre_load
    def normalize_input(self, data, **kwargs):
        # Upper case airport codes
        if "origin" in data and isinstance(data["origin"], str):
            data["origin"] = data["origin"].upper()
        if "destination" in data and isinstance(data["destination"], str):
            data["destination"] = data["destination"].upper()
        return data

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data["date"] < date.today():
             raise ValidationError("Departure date cannot be in the past", field_name="date")
        
        if data.get("return_date") and data["return_date"] < data["date"]:
             raise ValidationError("Return date cannot be before departure date", field_name="return_date")
