from marshmallow import Schema, fields, validate, validates, ValidationError
from src.models.medication import MedicationRoute, MedicationFrequency


class MedicationSchema(Schema):
    """Schema for serializing and deserializing Medication model instances"""

    id = fields.Int(dump_only=True)
    patient_id = fields.Int(required=True)
    name = fields.Str(required=True)
    dosage = fields.Str(required=True)
    dosage_unit = fields.Str(required=True)
    route = fields.Str(
        required=True,
        validate=validate.OneOf([route.value for route in MedicationRoute]),
    )
    frequency = fields.Str(
        required=True,
        validate=validate.OneOf([freq.value for freq in MedicationFrequency]),
    )
    custom_frequency = fields.Str()
    indication = fields.Str()
    prescriber = fields.Str()
    start_date = fields.Date(required=True)
    end_date = fields.Date()
    instructions = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Computed fields
    display_frequency = fields.Str(dump_only=True)
    is_expired = fields.Bool(dump_only=True)

    # Nested fields
    patient = fields.Nested("PatientSchema", only=["id", "full_name", "mrn"], dump_only=True)

    @validates("patient_id")
    def validate_patient_id(self, value):
        from src.models.patient import Patient
        from src import db

        patient = db.session.query(Patient).get(value)
        if not patient:
            raise ValidationError("Patient not found.")


class MedicationListSchema(Schema):
    """Schema for medication list view with fewer fields"""

    id = fields.Int(dump_only=True)
    name = fields.Str()
    dosage = fields.Str()
    dosage_unit = fields.Str()
    route = fields.Str()
    display_frequency = fields.Str()
    start_date = fields.Date()
    end_date = fields.Date()
    is_active = fields.Bool()
    is_expired = fields.Bool()


class MedicationUpdateSchema(MedicationSchema):
    """Schema for updating Medication instances"""

    patient_id = fields.Int()
    name = fields.Str()
    dosage = fields.Str()
    dosage_unit = fields.Str()
    route = fields.Str(validate=validate.OneOf([route.value for route in MedicationRoute]))
    frequency = fields.Str(validate=validate.OneOf([freq.value for freq in MedicationFrequency]))
