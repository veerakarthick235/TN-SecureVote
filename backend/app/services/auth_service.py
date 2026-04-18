"""
Authentication Service for TN SecureVote
Handles voter registration, OTP verification, biometric simulation, and JWT token issuance.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.voter import Voter


class AuthService:
    """Handles voter authentication lifecycle."""

    @staticmethod
    def hash_aadhaar(aadhaar: str) -> str:
        """Hash Aadhaar number with salt for storage. Never store raw Aadhaar."""
        salt = "tn-securevote-aadhaar-salt"
        return hashlib.sha256(f"{salt}|{aadhaar}".encode()).hexdigest()

    @staticmethod
    def hash_phone(phone: str) -> str:
        """Hash phone number for storage."""
        salt = "tn-securevote-phone-salt"
        return hashlib.sha256(f"{salt}|{phone}".encode()).hexdigest()

    @staticmethod
    def generate_otp() -> Tuple[str, datetime]:
        """Generate a 6-digit OTP with expiry."""
        otp = f"{secrets.randbelow(900000) + 100000}"
        expires = datetime.utcnow() + timedelta(minutes=5)
        return otp, expires

    @staticmethod
    def register_voter(
        db: Session,
        aadhaar: str,
        name: str,
        district: str,
        constituency: str,
        phone: str,
    ) -> Tuple[Optional[Voter], str]:
        """Register a new voter. Returns (voter, otp) or (None, error_message)."""
        aadhaar_hash = AuthService.hash_aadhaar(aadhaar)

        # Check for duplicate registration
        existing = db.query(Voter).filter(Voter.aadhaar_hash == aadhaar_hash).first()
        if existing:
            return None, "VOTER_ALREADY_REGISTERED"

        otp, otp_expires = AuthService.generate_otp()

        voter = Voter(
            id=str(uuid.uuid4()),
            aadhaar_hash=aadhaar_hash,
            name=name,
            district=district,
            constituency=constituency,
            phone_hash=AuthService.hash_phone(phone),
            otp_secret=hashlib.sha256(otp.encode()).hexdigest(),
            otp_expires_at=otp_expires,
        )
        db.add(voter)
        db.commit()
        db.refresh(voter)

        return voter, otp

    @staticmethod
    def verify_otp(db: Session, voter_id: str, otp: str) -> Tuple[bool, str]:
        """Verify OTP for a voter."""
        voter = db.query(Voter).filter(Voter.id == voter_id).first()
        if not voter:
            return False, "VOTER_NOT_FOUND"

        if voter.otp_expires_at and voter.otp_expires_at < datetime.utcnow():
            return False, "OTP_EXPIRED"

        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        if voter.otp_secret != otp_hash:
            return False, "INVALID_OTP"

        voter.is_verified = True
        voter.otp_secret = None
        voter.otp_expires_at = None
        db.commit()

        return True, "OTP_VERIFIED"

    @staticmethod
    def verify_biometric(db: Session, voter_id: str, fingerprint_hash: str) -> Tuple[bool, str]:
        """
        Simulate biometric verification.
        In production: integrates with UIDAI/biometric hardware.
        In simulation: accepts any non-empty hash.
        """
        voter = db.query(Voter).filter(Voter.id == voter_id).first()
        if not voter:
            return False, "VOTER_NOT_FOUND"

        if not voter.is_verified:
            return False, "OTP_NOT_VERIFIED"

        # Simulation: accept any fingerprint hash with length >= 32
        if len(fingerprint_hash) < 32:
            return False, "INVALID_BIOMETRIC"

        return True, "BIOMETRIC_VERIFIED"

    @staticmethod
    def create_access_token(voter: Voter) -> str:
        """Create a JWT access token for authenticated voter."""
        payload = {
            "sub": voter.id,
            "name": voter.name,
            "district": voter.district,
            "constituency": voter.constituency,
            "is_demo": voter.is_demo,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except Exception:
            return None

    @staticmethod
    def create_demo_voter(db: Session, name: str = "Demo Voter") -> Voter:
        """Create a demo voter that bypasses authentication."""
        demo_id = str(uuid.uuid4())
        voter = Voter(
            id=demo_id,
            aadhaar_hash=hashlib.sha256(f"demo-{demo_id}".encode()).hexdigest(),
            name=name,
            district="Chennai",
            constituency="Mylapore",
            phone_hash=hashlib.sha256(f"demo-phone-{demo_id}".encode()).hexdigest(),
            is_eligible=True,
            is_verified=True,
            is_demo=True,
        )
        db.add(voter)
        db.commit()
        db.refresh(voter)
        return voter
