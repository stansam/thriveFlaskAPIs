from marshmallow import Schema, fields, post_dump, EXCLUDE, ValidationError
from datetime import datetime

class BaseSchema(Schema):
    id = fields.UUID(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    class Meta:
        unknown = EXCLUDE
        ordered = True

    def handle_error(self, error, data, **kwargs):
        raise ValidationError({
            "message": "Validation error",
            "errors": error.messages})
    
    @post_dump
    def removeNoneFields(self, data: dict, **kwargs) -> dict:
        return {k:v for k, v in data.items() if v is not None}
