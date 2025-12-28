from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class PriorityLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConsultationStatus(enum.Enum):
    PENDING = "pending"
    UNDER_SUPERVISION = "under_supervision"
    SOLVED = "solved"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    blood_group = Column(String(10))
    address = Column(Text)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    consultations = relationship("Consultation", back_populates="user", foreign_keys="Consultation.user_id")
    medical_histories = relationship("MedicalHistory", back_populates="user")


class MedicalHistory(Base):
    __tablename__ = "medical_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition = Column(String(255), nullable=False)
    diagnosis_date = Column(DateTime)
    notes = Column(Text)
    is_chronic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="medical_histories")


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms = Column(Text, nullable=False)
    image_path = Column(String(500))
    ai_response = Column(Text)
    priority = Column(Enum(PriorityLevel), default=PriorityLevel.LOW)
    first_aid_suggestions = Column(Text)
    recommended_specialization = Column(String(255))
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.PENDING)
    supervising_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supervision_notes = Column(Text, nullable=True)
    use_history = Column(Boolean, default=True)
    is_synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_offline = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="consultations", foreign_keys="Consultation.user_id")
    supervising_admin = relationship("User", foreign_keys="Consultation.supervising_admin_id")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=False)
    qualification = Column(String(255))
    phone = Column(String(20))
    hospital = Column(String(255))
    available_days = Column(String(255))
    fee = Column(Integer)
    address = Column(Text)
    latitude = Column(String(50))
    longitude = Column(String(50))


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100))  # government, private, clinic
    address = Column(Text, nullable=False)
    phone = Column(String(20))
    emergency_available = Column(Boolean, default=False)
    latitude = Column(String(50))
    longitude = Column(String(50))
    facilities = Column(Text)


class NGO(Base):
    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    services = Column(Text)
    address = Column(Text, nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    latitude = Column(String(50))
    longitude = Column(String(50))
    working_areas = Column(Text)
