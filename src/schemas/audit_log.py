from marshmallow import Schema, fields


class AuditLogSchema(Schema):
    """Schema for serializing and deserializing AuditLog model instances"""

    id = fields.Int(dump_only=True)
    user_id = fields.Int()
    action = fields.Str()
    resource_type = fields.Str()
    resource_id = fields.Int()
    details = fields.Dict()
    ip_address = fields.Str()
    user_agent = fields.Str()
    timestamp = fields.DateTime()

    # Nested fields
    user = fields.Nested("UserSchema", only=["id", "username", "full_name"], dump_only=True)
