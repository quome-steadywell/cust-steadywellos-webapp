from marshmallow import Schema, fields, validate, validates, ValidationError
from src.models.call import CallStatus


class CallSchema(Schema):
    """Schema for serializing and deserializing Call model instances"""

    id = fields.Int(dump_only=True)
    patient_id = fields.Int(required=True)
    conducted_by_id = fields.Int()
    scheduled_time = fields.DateTime(required=True)
    start_time = fields.DateTime(dump_only=True)
    end_time = fields.DateTime(dump_only=True)
    duration = fields.Float(dump_only=True)
    status = fields.Str(
        validate=validate.OneOf([status.value for status in CallStatus])
    )
    call_type = fields.Str(required=True)
    twilio_call_sid = fields.Str()
    recording_url = fields.Str()
    transcript = fields.Str()
    notes = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Computed fields
    is_overdue = fields.Bool(dump_only=True)

    # Nested fields
    patient = fields.Nested(
        "PatientSchema", only=["id", "full_name", "mrn", "phone_number"], dump_only=True
    )
    conducted_by = fields.Nested("UserSchema", only=["id", "full_name"], dump_only=True)
    assessment = fields.Nested("AssessmentSchema", exclude=["call_id"], dump_only=True)

    @validates("patient_id")
    def validate_patient_id(self, value):
        from src.models.patient import Patient
        from src import db

        patient = db.session.query(Patient).get(value)
        if not patient:
            raise ValidationError("Patient not found.")
        if not patient.is_active:
            raise ValidationError("Cannot schedule call for inactive patient.")

    @validates("conducted_by_id")
    def validate_conducted_by_id(self, value):
        from src.models.user import User, UserRole
        from src import db

        if value is not None:  # This field is optional
            user = db.session.query(User).get(value)
            if not user:
                raise ValidationError("User not found.")
            if user.role not in [UserRole.NURSE, UserRole.PHYSICIAN]:
                raise ValidationError(
                    "Calls can only be conducted by a nurse or physician."
                )


class CallListSchema(Schema):
    """Schema for call list view with fewer fields"""

    id = fields.Int(dump_only=True)
    patient = fields.Nested("PatientSchema", only=["id", "full_name"], dump_only=True)
    scheduled_time = fields.DateTime()
    status = fields.Str()
    call_type = fields.Str()
    duration = fields.Float()
    is_overdue = fields.Bool()


class CallUpdateSchema(Schema):
    """Schema for updating Call instances"""

    conducted_by_id = fields.Int()
    scheduled_time = fields.DateTime()
    status = fields.Str(
        validate=validate.OneOf([status.value for status in CallStatus])
    )
    notes = fields.Str()


class CallTranscriptSchema(Schema):
    """Schema for call transcripts"""

    call_id = fields.Int(required=True)
    transcript = fields.Str(required=True)
    recording_url = fields.Str()
