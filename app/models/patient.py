from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app import db

class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class ProtocolType(enum.Enum):
    CANCER = "cancer"
    HEART_FAILURE = "heart_failure"
    COPD = "copd"
    GENERAL = "general"

class Patient(db.Model):
    """Patient model for storing patient related details"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mrn = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(120), nullable=True)
    address = Column(Text, nullable=True)
    primary_diagnosis = Column(String(255), nullable=False)
    secondary_diagnoses = Column(Text, nullable=True)
    protocol_type = Column(Enum(ProtocolType), nullable=False)
    primary_nurse_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    advance_directive = Column(Boolean, default=False)
    dnr_status = Column(Boolean, default=False)
    allergies = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    primary_nurse = relationship("User", back_populates="patients")
    assessments = relationship("Assessment", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    calls = relationship("Call", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient {self.first_name} {self.last_name} (MRN: {self.mrn})>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = datetime.today().date()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    def last_assessment(self):
        if not self.assessments:
            return None
        return sorted(self.assessments, key=lambda a: a.assessment_date, reverse=True)[0]
