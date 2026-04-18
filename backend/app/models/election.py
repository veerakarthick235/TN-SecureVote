import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Election(Base):
    __tablename__ = "elections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(300), nullable=False)
    title_ta = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    description_ta = Column(Text, nullable=True)
    region = Column(String(100), nullable=False)
    election_type = Column(String(50), nullable=False)  # state, local, bypolls
    status = Column(String(20), default="upcoming")  # upcoming, active, closed, tallied
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_eligible_voters = Column(Integer, default=0)
    total_votes_cast = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_demo = Column(Boolean, default=False)

    candidates = relationship("Candidate", back_populates="election", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Election {self.title} ({self.status})>"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    election_id = Column(String(36), ForeignKey("elections.id"), nullable=False)
    name = Column(String(200), nullable=False)
    name_ta = Column(String(300), nullable=True)
    party = Column(String(200), nullable=False)
    party_ta = Column(String(300), nullable=True)
    symbol = Column(String(50), nullable=False)  # emoji symbol
    manifesto = Column(Text, nullable=True)
    candidate_index = Column(Integer, nullable=False)  # position on ballot
    created_at = Column(DateTime, default=datetime.utcnow)

    election = relationship("Election", back_populates="candidates")

    def __repr__(self):
        return f"<Candidate {self.name} - {self.party}>"
