from marshmallow import fields, validate
from app.schemas.base import BaseSchema

class TicketUploadSchema(BaseSchema):
    pnr_reference = fields.String(required=True, validate=validate.Length(min=3, max=20))
    eticket_number = fields.String(required=True, validate=validate.Length(min=5, max=50))
    
class VoidBookingSchema(BaseSchema):
    reason = fields.String(required=True, validate=validate.Length(min=5, max=255))
