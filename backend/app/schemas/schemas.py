from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Auth Schemas ---
class VoterRegisterRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    name: str
    district: str
    constituency: str
    phone: str = Field(..., min_length=10, max_length=10)


class VoterRegisterResponse(BaseModel):
    voter_id: str
    message: str
    otp_sent: bool


class OTPVerifyRequest(BaseModel):
    voter_id: str
    otp: str = Field(..., min_length=6, max_length=6)


class BiometricVerifyRequest(BaseModel):
    voter_id: str
    fingerprint_hash: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    voter_id: str
    name: str
    is_demo: bool = False


class DemoLoginRequest(BaseModel):
    demo_voter_name: str = "Demo Voter"


# --- Election Schemas ---
class CandidateResponse(BaseModel):
    id: str
    name: str
    name_ta: Optional[str] = None
    party: str
    party_ta: Optional[str] = None
    symbol: str
    candidate_index: int

    class Config:
        from_attributes = True


class ElectionResponse(BaseModel):
    id: str
    title: str
    title_ta: Optional[str] = None
    description: Optional[str] = None
    description_ta: Optional[str] = None
    region: str
    election_type: str
    status: str
    start_time: datetime
    end_time: datetime
    total_eligible_voters: int
    total_votes_cast: int
    candidates: List[CandidateResponse] = []

    class Config:
        from_attributes = True


class ElectionCreateRequest(BaseModel):
    title: str
    title_ta: Optional[str] = None
    description: Optional[str] = None
    description_ta: Optional[str] = None
    region: str
    election_type: str = "state"
    start_time: datetime
    end_time: datetime
    total_eligible_voters: int = 0


class CandidateCreateRequest(BaseModel):
    name: str
    name_ta: Optional[str] = None
    party: str
    party_ta: Optional[str] = None
    symbol: str
    candidate_index: int


# --- Vote Schemas ---
class BlindTokenRequest(BaseModel):
    election_id: str
    blinded_token: str  # base64-encoded blinded token from client


class BlindTokenResponse(BaseModel):
    signed_blinded_token: str  # base64-encoded signed blinded token
    election_public_key: str  # base64-encoded election public key


class VoteSubmitRequest(BaseModel):
    election_id: str
    encrypted_ballot: str  # JSON string of ElGamal ciphertext
    token_signature: str  # base64-encoded unblinded signature
    token_value: str  # base64-encoded original token
    zkp_proof: Optional[str] = None  # JSON string of ZKP proof


class VoteSubmitResponse(BaseModel):
    receipt_hash: str
    block_index: int
    block_hash: str
    timestamp: str
    message: str


class VoteReceiptResponse(BaseModel):
    receipt_hash: str
    block_index: int
    block_hash: str
    timestamp: str
    election_id: str
    is_verified: bool


class VoteVerifyRequest(BaseModel):
    receipt_hash: str


class VoteVerifyResponse(BaseModel):
    is_valid: bool
    receipt_hash: str
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    timestamp: Optional[str] = None
    message: str


# --- Audit Schemas ---
class BlockResponse(BaseModel):
    index: int
    timestamp: str
    vote_count: int
    previous_hash: str
    block_hash: str
    merkle_root: str


class ChainResponse(BaseModel):
    election_id: str
    total_blocks: int
    total_votes: int
    is_valid: bool
    blocks: List[BlockResponse]


class TallyResult(BaseModel):
    candidate_id: str
    candidate_name: str
    party: str
    vote_count: int
    percentage: float


class ElectionResultsResponse(BaseModel):
    election_id: str
    election_title: str
    status: str
    total_votes: int
    results: List[TallyResult]
    chain_verified: bool


class AuditLogResponse(BaseModel):
    id: str
    action: str
    actor_type: str
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Fraud Detection ---
class FraudAlertResponse(BaseModel):
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    description: str
    election_id: str
    timestamp: datetime
    details: Optional[dict] = None
