from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
import enum
from src import db

class MedicationRoute(enum.Enum):
    ORAL = "oral"
    SUBLINGUAL = "sublingual"
    TOPICAL = "topical"
    TRANSDERMAL = "transdermal"
    INHALATION = "inhalation"
    RECTAL = "rectal"
    SUBCUTANEOUS = "subcutaneous"
    INTRAMUSCULAR = "intramuscular"
    INTRAVENOUS = "intravenous"
    OTHER = "other"

class MedicationFrequency(enum.Enum):
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    EVERY_MORNING = "every_morning"
    EVERY_NIGHT = "every_night"
    EVERY_OTHER_DAY = "every_other_day"
    AS_NEEDED = "as_needed"
    WEEKLY = "weekly"
    OTHER = "other"

class Medication(db.Model):
    """Medication model for storing patient medications"""
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    dosage_unit = Column(String(50), nullable=False)
    route = Column(Enum(MedicationRoute), nullable=False)
    frequency = Column(Enum(MedicationFrequency), nullable=False)
    custom_frequency = Column(String(255), nullable=True)  # For 'other' frequency
    indication = Column(String(255), nullable=True)
    prescriber = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null means ongoing
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medications")
    
    def __repr__(self):
        return f"<Medication {self.name} {self.dosage}{self.dosage_unit} for Patient {self.patient_id}>"
    
    @property
    def display_frequency(self):
        if self.frequency == MedicationFrequency.OTHER and self.custom_frequency:
            return self.custom_frequency
        return self.frequency.value.replace('_', ' ').title()
    
    @property
    def is_expired(self):
        if not self.end_date:
            return False
        return self.end_date < datetime.now().date()
