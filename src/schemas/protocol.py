from marshmallow import Schema, fields, validate, validates, ValidationError
from src.models.patient import ProtocolType


class QuestionSchema(Schema):
    """Schema for protocol questions"""

    id = fields.Str(required=True)
    text = fields.Str(required=True)
    type = fields.Str(
        required=True, validate=validate.OneOf(["numeric", "text", "boolean", "choice"])
    )
    required = fields.Bool()
    symptom_type = fields.Str()
    min_value = fields.Float()
    max_value = fields.Float()
    choices = fields.List(fields.Str())
    follow_up_questions = fields.List(fields.Dict())


class InterventionSchema(Schema):
    """Schema for protocol interventions"""

    id = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    symptom_type = fields.Str()
    severity_threshold = fields.Float()
    instructions = fields.Str()


class DecisionNodeSchema(Schema):
    """Schema for decision tree nodes"""

    id = fields.Str(required=True)
    symptom_type = fields.Str(required=True)
    condition = fields.Str(required=True)
    value = fields.Float()
    next_node_id = fields.Str()
    intervention_ids = fields.List(fields.Str())


class ProtocolSchema(Schema):
    """Schema for serializing and deserializing Protocol model instances"""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    protocol_type = fields.Str(
        required=True,
        validate=validate.OneOf([protocol.value for protocol in ProtocolType]),
    )
    version = fields.Str(required=True)
    questions = fields.List(fields.Dict(), required=True)
    decision_tree = fields.List(fields.Dict(), required=True)
    interventions = fields.List(fields.Dict(), required=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates("version")
    def validate_version(self, value):
        from src.models.protocol import Protocol
        from src import db

        # Only validate if creating a new protocol
        if self.context.get("is_update") is not True:
            protocol_type = self.context.get("protocol_type")
            if protocol_type:
                # Check if version already exists for this protocol type
                existing = (
                    db.session.query(Protocol)
                    .filter(
                        Protocol.protocol_type == protocol_type,
                        Protocol.version == value,
                    )
                    .first()
                )

                if existing:
                    raise ValidationError(
                        f"Version {value} already exists for {protocol_type} protocol."
                    )


class ProtocolUpdateSchema(ProtocolSchema):
    """Schema for updating Protocol instances"""

    name = fields.Str()
    description = fields.Str()
    protocol_type = fields.Str(
        validate=validate.OneOf([protocol.value for protocol in ProtocolType])
    )
    version = fields.Str()
    questions = fields.List(fields.Dict())
    decision_tree = fields.List(fields.Dict())
    interventions = fields.List(fields.Dict())


class ProtocolListSchema(Schema):
    """Schema for protocol list view with fewer fields"""

    id = fields.Int(dump_only=True)
    name = fields.Str()
    protocol_type = fields.Str()
    version = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime()
