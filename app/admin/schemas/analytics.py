from marshmallow import fields, validates_schema, ValidationError
from app.schemas.base import BaseSchema
from datetime import date

class DashboardQuerySchema(BaseSchema):
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise ValidationError("Start date must be strictly before or equal to End date.")
