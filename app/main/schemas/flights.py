from marshmallow import fields, validate, pre_load, validates_schema, ValidationError
from app.schemas.base import BaseSchema
from datetime import date
from app.models.enums import TravelClass

class PassengerQuerySchema(BaseSchema):
    adults = fields.Integer(load_default=1, validate=validate.Range(min=1, max=9))
    children = fields.Integer(load_default=0, validate=validate.Range(min=0, max=9))
    infants = fields.Integer(load_default=0, validate=validate.Range(min=0, max=9))

class FlightSearchSchema(BaseSchema):
    origin = fields.String(required=True, validate=validate.Length(equal=3))
    destination = fields.String(required=True, validate=validate.Length(equal=3))
    date = fields.Date(required=True)
    return_date = fields.Date(load_default=None)
    passengers = fields.Nested(PassengerQuerySchema, load_default=lambda: {"adults": 1, "children": 0, "infants": 0})
    cabin_class = fields.String(load_default=TravelClass.ECONOMY.value, validate=validate.OneOf(TravelClass.list()))
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))

    @pre_load
    def normalize_input(self, data, **kwargs):
        if "origin" in data and isinstance(data["origin"], str):
            data["origin"] = data["origin"].upper()
        if "destination" in data and isinstance(data["destination"], str):
            data["destination"] = data["destination"].upper()
        if "currency" in data and isinstance(data["currency"], str):
            data["currency"] = data["currency"].upper()
        return data

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'date' in data and data['date'] < date.today():
             raise ValidationError("Departure date cannot be in the past", field_name="date")
        
        if data.get("return_date") and data.get("date") and data["return_date"] < data["date"]:
             raise ValidationError("Return date cannot be before departure date", field_name="return_date")
