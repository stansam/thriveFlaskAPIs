from marshmallow import fields, validate
from app.schemas.base import BaseSchema

class VerifyPaymentSchema(BaseSchema):
    status = fields.String(required=True, validate=validate.OneOf(['approved', 'rejected']))
    rejection_reason = fields.String(required=False, allow_none=True)
