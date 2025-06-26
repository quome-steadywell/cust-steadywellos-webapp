from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
import enum
from src import db


class CallStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    CANCELLED = "cancelled"


class Call(db.Model):
    """Call model for storing telephony interactions"""

    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    conducted_by_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Can be null for automated calls
    scheduled_time = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    status = Column(Enum(CallStatus), default=CallStatus.SCHEDULED, nullable=False)
    call_type = Column(
        String(50), nullable=False
    )  # E.g., 'assessment', 'follow-up', 'medication_check'
    twilio_call_sid = Column(String(50), nullable=True)
    recording_url = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="calls")
    conducted_by = relationship("User", back_populates="calls")
    assessment = relationship("Assessment", back_populates="call", uselist=False)

    def __repr__(self):
        return f"<Call {self.id} for Patient {self.patient_id} ({self.status.value})>"

    @property
    def is_overdue(self):
        return (
            self.status == CallStatus.SCHEDULED
            and self.scheduled_time < datetime.utcnow()
        )

    def update_status(self, status):
        self.status = status
        if status == CallStatus.IN_PROGRESS and not self.start_time:
            self.start_time = datetime.utcnow()
        elif status == CallStatus.COMPLETED and not self.end_time:
            self.end_time = datetime.utcnow()
            if self.start_time:
                self.duration = (self.end_time - self.start_time).total_seconds()
        db.session.commit()
