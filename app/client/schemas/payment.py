from marshmallow import fields, validate
from app.schemas import BaseSchema
from app.models.enums import PaymentMethod

class InvoicePaymentSchema(BaseSchema):
    payment_method = fields.Str(required=True, validate=validate.OneOf(PaymentMethod.list()))
    payment_proof_url = fields.URL(required=True)
    transaction_id = fields.Str(required=False, allow_none=True)
