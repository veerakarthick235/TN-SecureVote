"""Audit Router - Blockchain explorer, results, audit trail for judges and public."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import (
    ChainResponse,
    BlockResponse,
    ElectionResultsResponse,
    AuditLogResponse,
    FraudAlertResponse,
)
from app.services.vote_service import VoteService
from app.blockchain.chain import get_blockchain
from app.models.audit import AuditLog
from app.services.fraud_service import get_fraud_service

router = APIRouter(prefix="/api/audit", tags=["Audit & Results"])


@router.get("/results/{election_id}")
def get_election_results(election_id: str, db: Session = Depends(get_db)):
    """Get tallied results for an election. Publicly accessible."""
    results = VoteService.get_election_results(db, election_id)
    if not results:
        raise HTTPException(status_code=404, detail="ELECTION_NOT_FOUND")
    return results


@router.get("/blockchain/{election_id}")
def get_blockchain_state(election_id: str):
    """Get full blockchain state for an election. For judicial audit."""
    blockchain = get_blockchain(election_id)
    summary = blockchain.get_chain_summary()
    blocks = blockchain.get_all_blocks()
    return {
        **summary,
        "blocks": [
            {
                "index": b["index"],
                "timestamp": b["timestamp"],
                "vote_count": b["vote_count"],
                "previous_hash": b["previous_hash"],
                "block_hash": b["hash"],
                "merkle_root": b["merkle_root"],
            }
            for b in blocks
        ],
    }


@router.get("/chain-valid/{election_id}")
def validate_chain(election_id: str):
    """Validate blockchain integrity. Public endpoint."""
    blockchain = get_blockchain(election_id)
    is_valid = blockchain.validate_chain()
    summary = blockchain.get_chain_summary()
    return {
        "election_id": election_id,
        "is_valid": is_valid,
        "total_blocks": summary["total_blocks"],
        "total_votes": summary["total_votes"],
    }


@router.get("/trail/{election_id}")
def get_audit_trail(election_id: str, db: Session = Depends(get_db)):
    """Get audit trail for judges. Shows all actions related to election."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.election_id == election_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": log.id,
            "action": log.action,
            "actor_type": log.actor_type,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        }
        for log in logs
    ]


@router.get("/fraud-alerts")
def get_fraud_alerts(election_id: str = None):
    """Get AI-detected fraud alerts."""
    fraud = get_fraud_service()
    alerts = fraud.get_alerts(election_id)
    return {"alerts": alerts, "total": len(alerts)}


@router.post("/run-analysis/{election_id}")
def run_fraud_analysis(election_id: str):
    """Run Isolation Forest anomaly detection on election data."""
    fraud = get_fraud_service()
    anomalies = fraud.run_isolation_forest(election_id)
    return {
        "election_id": election_id,
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
    }
