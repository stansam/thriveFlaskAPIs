from marshmallow import Schema, fields, post_dump, EXCLUDE, ValidationError
from datetime import datetime
class BaseSchema(Schema):
    id = fields.UUID(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
    class Meta:
        unknown = EXCLUDE
        ordered = True
    def handle_error(self, error, **kwargs):
        raise ValidationError({
            "message": "Validation error",
            "errors": error})
    
    @post_dump(pass_many=False)
    def removeNoneFields(self, data: dict, **kwargs) -> dict:
        return {k:v for k, v in data.items if v is not None}
    
