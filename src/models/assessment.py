from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
import enum
from src import db

class FollowUpPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Assessment(db.Model):
    """Assessment model for storing patient assessments"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    protocol_id = Column(Integer, ForeignKey('protocols.id'), nullable=False)
    conducted_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=True)  # Optional link to a call
    assessment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    responses = Column(JSON, nullable=False)  # Structured responses to protocol questions
    symptoms = Column(JSON, nullable=False)  # Extracted symptoms with severity
    interventions = Column(JSON, nullable=True)  # Recommended interventions
    notes = Column(Text, nullable=True)  # Clinical notes
    follow_up_needed = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_priority = Column(Enum(FollowUpPriority), nullable=True)
    ai_guidance = Column(Text, nullable=True)  # RAG model generated guidance
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="assessments")
    protocol = relationship("Protocol", back_populates="assessments")
    conducted_by = relationship("User", back_populates="assessments")
    call = relationship("Call", back_populates="assessment")
    
    def __repr__(self):
        return f"<Assessment {self.id} for Patient {self.patient_id}>"
    
    def urgent_symptoms(self, threshold=7):
        """Return symptoms with severity above threshold"""
        if not self.symptoms:
            return {}
        return {symptom: severity for symptom, severity in self.symptoms.items() 
                if isinstance(severity, (int, float)) and severity >= threshold}
