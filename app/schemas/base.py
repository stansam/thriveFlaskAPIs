from marshmallow import Schema, fields, post_dump, EXCLUDE
from datetime import datetime
class BaseSchema(Schema):
    id = fields.UUID(dump_only=True)
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime(dump_only=True)
    class Meta:
        unknown = EXCLUDE
        ordered = True
    
    @post_dump(pass_many=False)
    def removeNoneFields(self, data: dict, **kwargs) -> dict:
        return {k:v for k, v in data.items if v is not None}
    
