import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from app.database import Base


class VoteToken(Base):
    __tablename__ = "vote_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    voter_id = Column(String(36), ForeignKey("voters.id"), nullable=False)
    election_id = Column(String(36), ForeignKey("elections.id"), nullable=False)
    blinded_token = Column(Text, nullable=False)
    signed_blinded_token = Column(Text, nullable=True)
    is_used = Column(Boolean, default=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<VoteToken voter={self.voter_id} used={self.is_used}>"


class EncryptedVote(Base):
    __tablename__ = "encrypted_votes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    election_id = Column(String(36), ForeignKey("elections.id"), nullable=False)
    encrypted_ballot = Column(Text, nullable=False)  # ElGamal ciphertext JSON
    token_signature = Column(Text, nullable=False)  # unblinded signature
    zkp_proof = Column(Text, nullable=True)  # ZKP proof JSON
    receipt_hash = Column(String(64), nullable=False, unique=True, index=True)
    block_index = Column(Integer, nullable=True)
    block_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EncryptedVote receipt={self.receipt_hash[:16]}...>"
