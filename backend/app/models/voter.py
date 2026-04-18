import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.database import Base


class Voter(Base):
    __tablename__ = "voters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aadhaar_hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    district = Column(String(100), nullable=False)
    constituency = Column(String(100), nullable=False)
    phone_hash = Column(String(64), nullable=False)
    is_eligible = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    otp_secret = Column(String(32), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    public_key = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_demo = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Voter {self.name} ({self.district})>"
