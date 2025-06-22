from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from src.models.patient import Gender, ProtocolType, AdvanceDirectiveStatus

class PatientSchema(Schema):
    """Schema for serializing and deserializing Patient model instances"""
    id = fields.Int(dump_only=True)
    mrn = fields.Str(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    date_of_birth = fields.Date(required=True)
    gender = fields.Str(required=True, validate=validate.OneOf([gender.value for gender in Gender]))
    phone_number = fields.Str(required=True)
    email = fields.Email()
    address = fields.Str()
    primary_diagnosis = fields.Str(required=True)
    secondary_diagnoses = fields.Str()
    protocol_type = fields.Str(required=True, validate=validate.OneOf([protocol.value for protocol in ProtocolType]))
    primary_nurse_id = fields.Int(required=True)
    emergency_contact_name = fields.Str()
    emergency_contact_phone = fields.Str()
    emergency_contact_relationship = fields.Str()
    emergency_contact_can_share_medical_info = fields.Bool()
    advance_directive = fields.Bool()
    advance_directive_status = fields.Str(validate=validate.OneOf([status.value for status in AdvanceDirectiveStatus]))
    dnr_status = fields.Bool()
    allergies = fields.Str()
    notes = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Computed fields
    full_name = fields.Str(dump_only=True)
    age = fields.Int(dump_only=True)
    
    # Nested fields
    primary_nurse = fields.Nested('UserSchema', only=['id', 'full_name', 'email'], dump_only=True)
    
    @validates('mrn')
    def validate_mrn(self, value):
        from src.models.patient import Patient
        from src import db
        
        # Check if MRN already exists (for new patients only)
        if self.context.get('is_update') is not True:
            if db.session.query(Patient).filter(Patient.mrn == value).first():
                raise ValidationError('MRN already exists.')
    
    @validates('primary_nurse_id')
    def validate_primary_nurse_id(self, value):
        from src.models.user import User, UserRole
        from src import db
        
        # Check if primary nurse exists and has NURSE role
        nurse = db.session.query(User).filter(User.id == value).first()
        if not nurse:
            raise ValidationError('Primary nurse not found.')
        if nurse.role != UserRole.NURSE and nurse.role != UserRole.PHYSICIAN:
            raise ValidationError('Primary care provider must be a nurse or physician.')

class PatientListSchema(Schema):
    """Schema for patient list view with fewer fields"""
    id = fields.Int(dump_only=True)
    mrn = fields.Str()
    full_name = fields.Str()
    age = fields.Int()
    primary_diagnosis = fields.Str()
    protocol_type = fields.Str()
    phone_number = fields.Str()
    primary_nurse = fields.Nested('UserSchema', only=['id', 'full_name'], dump_only=True)
    last_assessment_date = fields.DateTime(dump_only=True)
    is_active = fields.Bool()

class PatientUpdateSchema(PatientSchema):
    """Schema for updating Patient instances"""
    mrn = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()
    date_of_birth = fields.Date()
    gender = fields.Str(validate=validate.OneOf([gender.value for gender in Gender]))
    phone_number = fields.Str()
    protocol_type = fields.Str(validate=validate.OneOf([protocol.value for protocol in ProtocolType]))
    primary_nurse_id = fields.Int()
