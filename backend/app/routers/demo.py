"""Demo Router - Preloads sample election data and provides demo-mode utilities."""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.election import Election, Candidate
from app.models.voter import Voter
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

DEMO_ELECTION_ID = "demo-election-2026"


def get_demo_candidates():
    """Sample candidates with Tamil translations."""
    return [
        {
            "name": "DMK Candidate",
            "name_ta": "திமுக வேட்பாளர்",
            "party": "Dravida Munnetra Kazhagam (DMK)",
            "party_ta": "திராவிட முன்னேற்றக் கழகம் (திமுக)",
            "symbol": "☀️", # Rising Sun
            "candidate_index": 0,
        },
        {
            "name": "AIADMK Candidate",
            "name_ta": "அதிமுக வேட்பாளர்",
            "party": "All India Anna Dravida Munnetra Kazhagam (AIADMK)",
            "party_ta": "அனைத்திந்திய அண்ணா திராவிட முன்னேற்றக் கழகம் (அதிமுக)",
            "symbol": "🍃", # Two Leaves
            "candidate_index": 1,
        },
        {
            "name": "NTK Candidate",
            "name_ta": "நாம் தமிழர் வேட்பாளர்",
            "party": "Naam Tamilar Katchi (NTK)",
            "party_ta": "நாம் தமிழர் கட்சி (நாதக)",
            "symbol": "🌾", # Farmer
            "candidate_index": 2,
        },
        {
            "name": "PMK Candidate",
            "name_ta": "பாமக வேட்பாளர்",
            "party": "Pattali Makkal Katchi (PMK)",
            "party_ta": "பாட்டாளி மக்கள் கட்சி (பாமக)",
            "symbol": "🥭", # Mango
            "candidate_index": 3,
        },
    ]


@router.post("/setup")
def setup_demo(db: Session = Depends(get_db)):
    """Initialize demo mode with sample election and candidates."""
    # Check if demo already exists
    existing = db.query(Election).filter(Election.id == DEMO_ELECTION_ID).first()
    if existing:
        return {
            "message": "DEMO_ALREADY_EXISTS",
            "election_id": DEMO_ELECTION_ID,
            "status": existing.status,
        }

    # Create demo election
    election = Election(
        id=DEMO_ELECTION_ID,
        title="Tamil Nadu State Assembly Election 2026 (Demo)",
        title_ta="தமிழ்நாடு சட்டமன்றத் தேர்தல் 2026 (டெமோ)",
        description="Demonstration election for the TN SecureVote platform. "
                    "This election uses placeholder candidates and is for testing purposes only.",
        description_ta="TN SecureVote தளத்திற்கான ஆர்ப்பாட்டத் தேர்தல். "
                       "இந்தத் தேர்தல் placeholder வேட்பாளர்களைப் பயன்படுத்துகிறது மற்றும் சோதனை நோக்கங்களுக்காக மட்டுமே.",
        region="Tamil Nadu",
        election_type="state",
        status="active",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=1),
        total_eligible_voters=10000,
        is_demo=True,
    )
    db.add(election)

    # Add candidates
    for c in get_demo_candidates():
        candidate = Candidate(
            id=str(uuid.uuid4()),
            election_id=DEMO_ELECTION_ID,
            **c,
        )
        db.add(candidate)

    db.commit()

    return {
        "message": "DEMO_SETUP_COMPLETE",
        "election_id": DEMO_ELECTION_ID,
        "candidates": len(get_demo_candidates()),
    }


@router.post("/quick-vote")
def quick_vote(candidate_index: int = 0, db: Session = Depends(get_db)):
    """
    One-click demo vote: creates a voter, authenticates, gets token, encrypts vote,
    and submits - all in one call. For testing the full flow.
    """
    import json
    from app.services.crypto_service import (
        get_blind_sig_service,
        get_elgamal_service,
        get_receipt_service,
        get_zkp_service,
    )
    from app.services.vote_service import VoteService

    # 1. Create demo voter
    voter = AuthService.create_demo_voter(db, f"Demo Voter {uuid.uuid4().hex[:6]}")

    # 2. Ensure demo election exists
    election = db.query(Election).filter(Election.id == DEMO_ELECTION_ID).first()
    if not election:
        setup_demo(db)
        election = db.query(Election).filter(Election.id == DEMO_ELECTION_ID).first()

    # 3. Get blind token
    blind_sig = get_blind_sig_service()
    token_b64, _ = blind_sig.generate_token()
    blinded_token, r = blind_sig.blind_token(token_b64)

    # Sign blinded token
    signed_blinded, msg = VoteService.request_blind_token(
        db, voter.id, DEMO_ELECTION_ID, blinded_token
    )
    if not signed_blinded:
        return {"error": msg}

    # Unblind signature
    unblinded_sig = blind_sig.unblind_signature(signed_blinded, r)

    # 4. Encrypt vote
    elgamal = get_elgamal_service()
    encrypted = elgamal.encrypt(candidate_index)
    encrypted["candidate_index"] = candidate_index

    # 5. Generate ZKP
    zkp = get_zkp_service()
    proof = zkp.generate_proof(candidate_index, 4, DEMO_ELECTION_ID)

    # 6. Submit vote
    result, status = VoteService.submit_vote(
        db,
        DEMO_ELECTION_ID,
        json.dumps(encrypted),
        unblinded_sig,
        token_b64,
        json.dumps(proof),
    )

    if not result:
        return {"error": status}

    return {
        "message": "DEMO_VOTE_CAST",
        "voter_name": voter.name,
        "candidate_index": candidate_index,
        "receipt_hash": result["receipt_hash"],
        "block_index": result["block_index"],
        "block_hash": result["block_hash"],
        "token_verified": blind_sig.verify_token_signature(token_b64, unblinded_sig),
    }


@router.get("/status")
def demo_status(db: Session = Depends(get_db)):
    """Get demo mode status."""
    election = db.query(Election).filter(Election.id == DEMO_ELECTION_ID).first()
    if not election:
        return {"demo_active": False, "election_id": None}

    return {
        "demo_active": True,
        "election_id": DEMO_ELECTION_ID,
        "election_title": election.title,
        "status": election.status,
        "total_votes": election.total_votes_cast,
        "candidates": len(election.candidates),
    }


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    """Reset demo data."""
    from app.models.vote import VoteToken, EncryptedVote
    from app.blockchain.chain import reset_blockchain

    # Delete demo votes
    db.query(EncryptedVote).filter(EncryptedVote.election_id == DEMO_ELECTION_ID).delete()
    db.query(VoteToken).filter(VoteToken.election_id == DEMO_ELECTION_ID).delete()
    db.query(Candidate).filter(Candidate.election_id == DEMO_ELECTION_ID).delete()
    db.query(Election).filter(Election.id == DEMO_ELECTION_ID).delete()
    db.query(Voter).filter(Voter.is_demo == True).delete()
    db.commit()

    reset_blockchain(DEMO_ELECTION_ID)

    return {"message": "DEMO_RESET_COMPLETE"}
