"""Authentication Router - Handles voter registration, OTP, biometric, and demo login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import (
    VoterRegisterRequest,
    VoterRegisterResponse,
    OTPVerifyRequest,
    BiometricVerifyRequest,
    AuthTokenResponse,
    DemoLoginRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=VoterRegisterResponse)
def register_voter(req: VoterRegisterRequest, db: Session = Depends(get_db)):
    """Register a new voter using Aadhaar (simulated)."""
    voter, otp_or_error = AuthService.register_voter(
        db, req.aadhaar_number, req.name, req.district, req.constituency, req.phone
    )
    if voter is None:
        raise HTTPException(status_code=400, detail=otp_or_error)

    # In production, OTP is sent via SMS. In demo, we return it.
    return VoterRegisterResponse(
        voter_id=voter.id,
        message=f"OTP sent to registered mobile. (Demo OTP: {otp_or_error})",
        otp_sent=True,
    )


@router.post("/verify-otp")
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP sent to voter's phone."""
    success, message = AuthService.verify_otp(db, req.voter_id, req.otp)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message, "status": "verified"}


@router.post("/biometric")
def verify_biometric(req: BiometricVerifyRequest, db: Session = Depends(get_db)):
    """Verify biometric (simulated fingerprint)."""
    success, message = AuthService.verify_biometric(db, req.voter_id, req.fingerprint_hash)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Issue JWT after full verification
    from app.models.voter import Voter
    voter = db.query(Voter).filter(Voter.id == req.voter_id).first()
    token = AuthService.create_access_token(voter)

    return AuthTokenResponse(
        access_token=token,
        voter_id=voter.id,
        name=voter.name,
        is_demo=voter.is_demo,
    )


@router.post("/demo-login", response_model=AuthTokenResponse)
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """Demo mode: bypass authentication entirely."""
    voter = AuthService.create_demo_voter(db, req.demo_voter_name)
    token = AuthService.create_access_token(voter)
    return AuthTokenResponse(
        access_token=token,
        voter_id=voter.id,
        name=voter.name,
        is_demo=True,
    )


@router.get("/me")
def get_current_user(token: str):
    """Get current user info from JWT token."""
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    return {
        "voter_id": payload.get("sub"),
        "name": payload.get("name"),
        "district": payload.get("district"),
        "constituency": payload.get("constituency"),
        "is_demo": payload.get("is_demo", False),
    }
