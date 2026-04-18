"""Election & Admin Router - CRUD for elections and candidates."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import (
    ElectionResponse,
    ElectionCreateRequest,
    CandidateCreateRequest,
    CandidateResponse,
)
from app.models.election import Election, Candidate

router = APIRouter(prefix="/api/election", tags=["Election Management"])


@router.get("/active", response_model=List[ElectionResponse])
def get_active_elections(db: Session = Depends(get_db)):
    """Get all active elections."""
    elections = db.query(Election).filter(Election.status == "active").all()
    return elections


@router.get("/all")
def get_all_elections(db: Session = Depends(get_db)):
    """Get all elections (admin)."""
    elections = db.query(Election).order_by(Election.created_at.desc()).all()
    result = []
    for e in elections:
        result.append({
            "id": e.id,
            "title": e.title,
            "title_ta": e.title_ta,
            "description": e.description,
            "region": e.region,
            "election_type": e.election_type,
            "status": e.status,
            "start_time": e.start_time.isoformat() if e.start_time else "",
            "end_time": e.end_time.isoformat() if e.end_time else "",
            "total_eligible_voters": e.total_eligible_voters,
            "total_votes_cast": e.total_votes_cast,
            "is_demo": e.is_demo,
            "candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "name_ta": c.name_ta,
                    "party": c.party,
                    "party_ta": c.party_ta,
                    "symbol": c.symbol,
                    "candidate_index": c.candidate_index,
                }
                for c in e.candidates
            ],
        })
    return result


@router.get("/{election_id}")
def get_election(election_id: str, db: Session = Depends(get_db)):
    """Get election details with candidates."""
    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="ELECTION_NOT_FOUND")
    return {
        "id": election.id,
        "title": election.title,
        "title_ta": election.title_ta,
        "description": election.description,
        "description_ta": election.description_ta,
        "region": election.region,
        "election_type": election.election_type,
        "status": election.status,
        "start_time": election.start_time.isoformat(),
        "end_time": election.end_time.isoformat(),
        "total_eligible_voters": election.total_eligible_voters,
        "total_votes_cast": election.total_votes_cast,
        "candidates": [
            {
                "id": c.id,
                "name": c.name,
                "name_ta": c.name_ta,
                "party": c.party,
                "party_ta": c.party_ta,
                "symbol": c.symbol,
                "candidate_index": c.candidate_index,
            }
            for c in election.candidates
        ],
    }


@router.get("/{election_id}/candidates")
def get_candidates(election_id: str, db: Session = Depends(get_db)):
    """Get candidates for an election."""
    candidates = (
        db.query(Candidate)
        .filter(Candidate.election_id == election_id)
        .order_by(Candidate.candidate_index)
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "name_ta": c.name_ta,
            "party": c.party,
            "party_ta": c.party_ta,
            "symbol": c.symbol,
            "candidate_index": c.candidate_index,
        }
        for c in candidates
    ]


@router.post("/create")
def create_election(req: ElectionCreateRequest, db: Session = Depends(get_db)):
    """Create a new election (admin)."""
    election = Election(
        id=str(uuid.uuid4()),
        title=req.title,
        title_ta=req.title_ta,
        description=req.description,
        description_ta=req.description_ta,
        region=req.region,
        election_type=req.election_type,
        status="upcoming",
        start_time=req.start_time,
        end_time=req.end_time,
        total_eligible_voters=req.total_eligible_voters,
    )
    db.add(election)
    db.commit()
    db.refresh(election)
    return {"id": election.id, "message": "ELECTION_CREATED"}


@router.post("/{election_id}/candidate")
def add_candidate(
    election_id: str,
    req: CandidateCreateRequest,
    db: Session = Depends(get_db),
):
    """Add a candidate to an election (admin)."""
    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="ELECTION_NOT_FOUND")

    candidate = Candidate(
        id=str(uuid.uuid4()),
        election_id=election_id,
        name=req.name,
        name_ta=req.name_ta,
        party=req.party,
        party_ta=req.party_ta,
        symbol=req.symbol,
        candidate_index=req.candidate_index,
    )
    db.add(candidate)
    db.commit()
    return {"id": candidate.id, "message": "CANDIDATE_ADDED"}


@router.put("/{election_id}/status/{status}")
def update_election_status(
    election_id: str, status: str, db: Session = Depends(get_db)
):
    """Update election status (admin): upcoming → active → closed → tallied."""
    valid_statuses = ["upcoming", "active", "closed", "tallied"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {valid_statuses}")

    election = db.query(Election).filter(Election.id == election_id).first()
    if not election:
        raise HTTPException(status_code=404, detail="ELECTION_NOT_FOUND")

    election.status = status
    db.commit()
    return {"id": election_id, "status": status, "message": "STATUS_UPDATED"}
