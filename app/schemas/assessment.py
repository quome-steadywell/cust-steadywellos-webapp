from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.assessment import FollowUpPriority

class AssessmentSchema(Schema):
    """Schema for serializing and deserializing Assessment model instances"""
    id = fields.Int(dump_only=True)
    patient_id = fields.Int(required=True)
    protocol_id = fields.Int(required=True)
    conducted_by_id = fields.Int(required=True)
    call_id = fields.Int()
    assessment_date = fields.DateTime(required=True)
    responses = fields.Dict(required=True)  # Complex nested structure for responses
    symptoms = fields.Dict(required=True)  # Extracted symptoms with severity
    interventions = fields.List(fields.Dict())  # Recommended interventions
    notes = fields.Str()
    follow_up_needed = fields.Bool()
    follow_up_date = fields.DateTime()
    follow_up_priority = fields.Str(validate=validate.OneOf([priority.value for priority in FollowUpPriority]))
    ai_guidance = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Nested fields
    patient = fields.Nested('PatientSchema', only=['id', 'full_name', 'mrn'], dump_only=True)
    protocol = fields.Nested('ProtocolSchema', only=['id', 'name', 'protocol_type'], dump_only=True)
    conducted_by = fields.Nested('UserSchema', only=['id', 'full_name'], dump_only=True)
    
    @validates('patient_id')
    def validate_patient_id(self, value):
        from app.models.patient import Patient
        from app import db
        
        patient = db.session.query(Patient).get(value)
        if not patient:
            raise ValidationError('Patient not found.')
    
    @validates('protocol_id')
    def validate_protocol_id(self, value):
        from app.models.protocol import Protocol
        from app import db
        
        protocol = db.session.query(Protocol).get(value)
        if not protocol:
            raise ValidationError('Protocol not found.')
        if not protocol.is_active:
            raise ValidationError('Protocol is not active.')
    
    @validates('conducted_by_id')
    def validate_conducted_by_id(self, value):
        from app.models.user import User, UserRole
        from app import db
        
        user = db.session.query(User).get(value)
        if not user:
            raise ValidationError('User not found.')
        if user.role not in [UserRole.NURSE, UserRole.PHYSICIAN]:
            raise ValidationError('Assessment can only be conducted by a nurse or physician.')

class AssessmentListSchema(Schema):
    """Schema for assessment list view with fewer fields"""
    id = fields.Int(dump_only=True)
    patient = fields.Nested('PatientSchema', only=['id', 'full_name', 'mrn'], dump_only=True)
    assessment_date = fields.DateTime()
    follow_up_needed = fields.Bool()
    follow_up_priority = fields.Str()
    protocol = fields.Nested('ProtocolSchema', only=['id', 'name', 'protocol_type'], dump_only=True)

class AssessmentUpdateSchema(Schema):
    """Schema for updating Assessment instances"""
    notes = fields.Str()
    follow_up_needed = fields.Bool()
    follow_up_date = fields.DateTime()
    follow_up_priority = fields.Str(validate=validate.OneOf([priority.value for priority in FollowUpPriority]))
