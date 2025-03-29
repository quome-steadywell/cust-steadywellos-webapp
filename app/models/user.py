from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, bcrypt
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    NURSE = "nurse"
    PHYSICIAN = "physician"
    CAREGIVER = "caregiver"

class User(db.Model):
    """User model for storing user related details"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    _password = Column("password", String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.NURSE)
    phone_number = Column(String(20), nullable=True)
    license_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    login_attempts = Column(Integer, default=0)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = relationship("Patient", back_populates="primary_nurse")
    assessments = relationship("Assessment", back_populates="conducted_by")
    calls = relationship("Call", back_populates="conducted_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    @hybrid_property
    def password(self):
        return self._password
    
    @password.setter
    def password(self, password):
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self._password, password)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def increment_login_attempts(self):
        self.login_attempts += 1
        db.session.commit()
    
    def reset_login_attempts(self):
        self.login_attempts = 0
        self.last_login_at = datetime.utcnow()
        db.session.commit()
        
    def is_account_locked(self, max_attempts=5):
        return self.login_attempts >= max_attempts
