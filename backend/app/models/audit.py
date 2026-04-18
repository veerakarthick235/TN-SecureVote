import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    election_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    actor_type = Column(String(20), nullable=False)  # system, voter, admin, judge
    actor_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.actor_type}>"


class BlockchainState(Base):
    __tablename__ = "blockchain_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    election_id = Column(String(36), nullable=False, index=True)
    chain_json = Column(Text, nullable=False)  # serialized blockchain
    last_block_hash = Column(String(64), nullable=False)
    total_blocks = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
