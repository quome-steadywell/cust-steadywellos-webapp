from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from src import db
from src.models.patient import ProtocolType

class Protocol(db.Model):
    """Protocol model for storing clinical protocols"""
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    protocol_type = Column(Enum(ProtocolType), nullable=False)
    version = Column(String(20), nullable=False)
    questions = Column(JSON, nullable=False)  # Structured question set
    decision_tree = Column(JSON, nullable=False)  # Decision tree for triage
    interventions = Column(JSON, nullable=False)  # Suggested interventions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assessments = relationship("Assessment", back_populates="protocol")
    
    def __repr__(self):
        return f"<Protocol {self.name} v{self.version}>"
    
    @classmethod
    def get_latest_active_protocol(cls, protocol_type):
        """Get the latest active protocol for a given type"""
        return cls.query.filter_by(
            protocol_type=protocol_type,
            is_active=True
        ).order_by(cls.version.desc()).first()
