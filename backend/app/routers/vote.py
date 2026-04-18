"""Vote Router - Handles token issuance, vote submission, receipt, and verification."""
import json
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.schemas import (
    BlindTokenRequest,
    BlindTokenResponse,
    VoteSubmitRequest,
    VoteSubmitResponse,
    VoteVerifyRequest,
    VoteVerifyResponse,
    VoteReceiptResponse,
)
from app.services.vote_service import VoteService
from app.services.auth_service import AuthService
from app.services.crypto_service import get_blind_sig_service, get_elgamal_service
from app.services.fraud_service import get_fraud_service
from datetime import datetime

router = APIRouter(prefix="/api/vote", tags=["Voting"])


def get_voter_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract voter_id from JWT in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="MISSING_AUTH")
    token = authorization.replace("Bearer ", "")
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    return payload["sub"]


@router.post("/request-token", response_model=BlindTokenResponse)
def request_blind_token(
    req: BlindTokenRequest,
    voter_id: str = Depends(get_voter_id),
    db: Session = Depends(get_db),
):
    """
    Request a blind-signed voting token.
    The voter sends a blinded token; the authority signs it without seeing the actual token.
    This breaks the link between voter identity and vote.
    """
    signed, message = VoteService.request_blind_token(
        db, voter_id, req.election_id, req.blinded_token
    )
    if signed is None:
        raise HTTPException(status_code=400, detail=message)

    # Return signed token + election public key for vote encryption
    elgamal = get_elgamal_service()
    pub_params = elgamal.get_public_params()

    return BlindTokenResponse(
        signed_blinded_token=signed,
        election_public_key=json.dumps(pub_params),
    )


@router.get("/public-params")
def get_public_params():
    """Get public cryptographic parameters for client-side operations."""
    blind_sig = get_blind_sig_service()
    elgamal = get_elgamal_service()
    return {
        "rsa": blind_sig.get_public_params(),
        "elgamal": elgamal.get_public_params(),
    }


@router.post("/submit", response_model=VoteSubmitResponse)
def submit_vote(
    req: VoteSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    Submit an encrypted vote with a valid blind-signed token.
    NOTE: No authentication header required - the token IS the authentication.
    This preserves anonymity (vote cannot be linked to voter identity).
    """
    result, message = VoteService.submit_vote(
        db,
        req.election_id,
        req.encrypted_ballot,
        req.token_signature,
        req.token_value,
        req.zkp_proof,
    )
    if result is None:
        raise HTTPException(status_code=400, detail=message)

    # Record for fraud detection
    fraud = get_fraud_service()
    fraud.record_vote_event(
        election_id=req.election_id,
        ip_address="127.0.0.1",  # In production: from request headers
        timestamp=datetime.utcnow(),
    )

    return VoteSubmitResponse(**result)


@router.post("/verify", response_model=VoteVerifyResponse)
def verify_vote(req: VoteVerifyRequest, db: Session = Depends(get_db)):
    """Verify a vote exists on the blockchain using its receipt hash."""
    result, message = VoteService.verify_vote(db, req.receipt_hash)
    if result is None:
        return VoteVerifyResponse(
            is_valid=False,
            receipt_hash=req.receipt_hash,
            message="VOTE_NOT_FOUND",
        )
    return VoteVerifyResponse(
        is_valid=result["is_valid"],
        receipt_hash=result["receipt_hash"],
        block_index=result["block_index"],
        block_hash=result["block_hash"],
        timestamp=result["timestamp"],
        message="VOTE_VERIFIED" if result["is_valid"] else "VERIFICATION_FAILED",
    )


@router.get("/receipt/{receipt_hash}", response_model=VoteReceiptResponse)
def get_receipt(receipt_hash: str, db: Session = Depends(get_db)):
    """Get vote receipt by hash."""
    result = VoteService.get_receipt(db, receipt_hash)
    if not result:
        raise HTTPException(status_code=404, detail="RECEIPT_NOT_FOUND")
    return VoteReceiptResponse(**result)
