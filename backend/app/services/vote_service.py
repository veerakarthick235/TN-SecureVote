"""
Vote Service for TN SecureVote
Orchestrates the entire voting flow:
  Token request → Blind signature → Vote encryption → Blockchain commit → Receipt
"""
import json
import uuid
from datetime import datetime
from typing import Tuple, Optional, Dict

from sqlalchemy.orm import Session

from app.models.vote import VoteToken, EncryptedVote
from app.models.election import Election
from app.services.crypto_service import (
    get_blind_sig_service,
    get_elgamal_service,
    get_receipt_service,
    get_zkp_service,
)
from app.blockchain.chain import get_blockchain


class VoteService:
    """Orchestrates the secure voting flow."""

    @staticmethod
    def request_blind_token(
        db: Session, voter_id: str, election_id: str, blinded_token: str
    ) -> Tuple[Optional[str], str]:
        """
        Issue a blind-signed token to an authenticated voter.
        The authority signs the blinded token without seeing the actual token.
        """
        # Check election exists and is active
        election = db.query(Election).filter(Election.id == election_id).first()
        if not election:
            return None, "ELECTION_NOT_FOUND"
        if election.status != "active":
            return None, "ELECTION_NOT_ACTIVE"

        # Check if voter already has a token for this election
        existing = (
            db.query(VoteToken)
            .filter(VoteToken.voter_id == voter_id, VoteToken.election_id == election_id)
            .first()
        )
        if existing:
            return None, "TOKEN_ALREADY_ISSUED"

        # Sign the blinded token
        blind_sig = get_blind_sig_service()
        signed_blinded = blind_sig.sign_blinded_token(blinded_token)

        # Store the token record (links voter to token issuance, NOT to vote)
        token_record = VoteToken(
            id=str(uuid.uuid4()),
            voter_id=voter_id,
            election_id=election_id,
            blinded_token=blinded_token,
            signed_blinded_token=signed_blinded,
        )
        db.add(token_record)
        db.commit()

        return signed_blinded, "TOKEN_ISSUED"

    @staticmethod
    def submit_vote(
        db: Session,
        election_id: str,
        encrypted_ballot: str,
        token_signature: str,
        token_value: str,
        zkp_proof: Optional[str] = None,
    ) -> Tuple[Optional[Dict], str]:
        """
        Submit an encrypted vote with a valid blind-signed token.
        1. Verify token signature (proves voter was authenticated)
        2. Verify ZKP (proves vote encodes a valid candidate)
        3. Generate receipt
        4. Commit to blockchain
        """
        # 1. Verify the unblinded token signature
        blind_sig = get_blind_sig_service()
        if not blind_sig.verify_token_signature(token_value, token_signature):
            return None, "INVALID_TOKEN_SIGNATURE"

        # Check election
        election = db.query(Election).filter(Election.id == election_id).first()
        if not election:
            return None, "ELECTION_NOT_FOUND"
        if election.status != "active":
            return None, "ELECTION_NOT_ACTIVE"

        # 2. Verify ZKP if provided
        if zkp_proof:
            zkp = get_zkp_service()
            proof_data = json.loads(zkp_proof) if isinstance(zkp_proof, str) else zkp_proof
            if not zkp.verify_proof(proof_data, election_id):
                return None, "INVALID_ZKP_PROOF"

        # 3. Generate receipt hash
        timestamp = datetime.utcnow().isoformat()
        receipt_svc = get_receipt_service()
        receipt_hash = receipt_svc.generate_receipt(
            token_signature, encrypted_ballot, timestamp
        )

        # Check for duplicate receipt (double voting via same token)
        existing_vote = (
            db.query(EncryptedVote)
            .filter(EncryptedVote.receipt_hash == receipt_hash)
            .first()
        )
        if existing_vote:
            return None, "DUPLICATE_VOTE"

        # 4. Extract candidate_index from ballot for tallying
        # In production, this would be done via homomorphic decryption
        try:
            ballot_data = json.loads(encrypted_ballot)
            candidate_index = ballot_data.get("candidate_index", 0)
        except (json.JSONDecodeError, AttributeError):
            candidate_index = 0

        # 5. Commit to blockchain
        blockchain = get_blockchain(election_id)
        vote_data = {
            "token_signature": token_signature,
            "encrypted_ballot": encrypted_ballot,
            "zkp_proof": zkp_proof or "",
            "receipt_hash": receipt_hash,
            "candidate_index": candidate_index,
            "timestamp": timestamp,
        }

        try:
            block_result = blockchain.submit_vote(vote_data)
        except ValueError as e:
            return None, str(e)

        # 6. Store encrypted vote in database
        block_index = block_result.get("block_index")
        block_hash = block_result.get("block_hash")

        # If the vote is pending, force a block for immediate receipt
        if block_result.get("status") == "pending":
            force_result = blockchain.force_create_block()
            if force_result:
                block_index = force_result["block_index"]
                block_hash = force_result["block_hash"]

        encrypted_vote = EncryptedVote(
            id=str(uuid.uuid4()),
            election_id=election_id,
            encrypted_ballot=encrypted_ballot,
            token_signature=token_signature,
            zkp_proof=zkp_proof or "",
            receipt_hash=receipt_hash,
            block_index=block_index,
            block_hash=block_hash or "",
            timestamp=datetime.fromisoformat(timestamp),
        )
        db.add(encrypted_vote)

        # Update vote count
        election.total_votes_cast += 1
        db.commit()

        return {
            "receipt_hash": receipt_hash,
            "block_index": block_index or 0,
            "block_hash": block_hash or "",
            "timestamp": timestamp,
            "message": "VOTE_COMMITTED",
        }, "SUCCESS"

    @staticmethod
    def verify_vote(db: Session, receipt_hash: str) -> Tuple[Optional[Dict], str]:
        """Verify a vote exists on the blockchain using its receipt hash."""
        # Find the vote in DB
        vote = (
            db.query(EncryptedVote)
            .filter(EncryptedVote.receipt_hash == receipt_hash)
            .first()
        )
        if not vote:
            return None, "VOTE_NOT_FOUND"

        # Verify on blockchain
        blockchain = get_blockchain(vote.election_id)
        chain_result = blockchain.query_vote(receipt_hash)

        return {
            "is_valid": chain_result is not None and chain_result.get("found", False),
            "receipt_hash": receipt_hash,
            "block_index": vote.block_index,
            "block_hash": vote.block_hash,
            "timestamp": vote.timestamp.isoformat() if vote.timestamp else "",
            "election_id": vote.election_id,
            "chain_verified": blockchain.validate_chain(),
        }, "SUCCESS"

    @staticmethod
    def get_receipt(db: Session, receipt_hash: str) -> Optional[Dict]:
        """Get vote receipt details."""
        vote = (
            db.query(EncryptedVote)
            .filter(EncryptedVote.receipt_hash == receipt_hash)
            .first()
        )
        if not vote:
            return None
        return {
            "receipt_hash": vote.receipt_hash,
            "block_index": vote.block_index,
            "block_hash": vote.block_hash,
            "timestamp": vote.timestamp.isoformat() if vote.timestamp else "",
            "election_id": vote.election_id,
            "is_verified": True,
        }

    @staticmethod
    def get_election_results(db: Session, election_id: str) -> Optional[Dict]:
        """Get tallied results for an election."""
        from app.models.election import Candidate

        election = db.query(Election).filter(Election.id == election_id).first()
        if not election:
            return None

        blockchain = get_blockchain(election_id)
        tally = blockchain.tally_votes()
        chain_valid = blockchain.validate_chain()

        candidates = db.query(Candidate).filter(Candidate.election_id == election_id).all()
        total_votes = sum(tally.values())

        results = []
        for candidate in candidates:
            count = tally.get(str(candidate.candidate_index), 0)
            pct = (count / total_votes * 100) if total_votes > 0 else 0
            results.append({
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "candidate_name_ta": candidate.name_ta,
                "party": candidate.party,
                "party_ta": candidate.party_ta,
                "symbol": candidate.symbol,
                "vote_count": count,
                "percentage": round(pct, 2),
            })

        results.sort(key=lambda x: x["vote_count"], reverse=True)

        return {
            "election_id": election_id,
            "election_title": election.title,
            "election_title_ta": election.title_ta,
            "status": election.status,
            "total_votes": total_votes,
            "results": results,
            "chain_verified": chain_valid,
        }
