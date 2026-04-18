"""
Blockchain Simulation for TN SecureVote
Simulates Hyperledger Fabric with:
  - Block structure with Merkle trees
  - PBFT consensus simulation
  - Chaincode functions (submitVote, queryVote, tally)
  - Chain validation and integrity checks
"""
import hashlib
import json
import time
from typing import List, Dict, Optional, Any
from datetime import datetime


class MerkleTree:
    """Merkle tree for vote integrity verification within a block."""

    @staticmethod
    def compute_root(data_list: List[str]) -> str:
        if not data_list:
            return hashlib.sha256(b"empty").hexdigest()

        leaves = [hashlib.sha256(d.encode()).hexdigest() for d in data_list]

        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            next_level = []
            for i in range(0, len(leaves), 2):
                combined = leaves[i] + leaves[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            leaves = next_level

        return leaves[0]

    @staticmethod
    def verify_inclusion(data: str, proof: List[Dict], root: str) -> bool:
        """Verify that a data item is included in the Merkle tree."""
        current = hashlib.sha256(data.encode()).hexdigest()
        for step in proof:
            if step["position"] == "left":
                combined = step["hash"] + current
            else:
                combined = current + step["hash"]
            current = hashlib.sha256(combined.encode()).hexdigest()
        return current == root


class Block:
    """A single block in the voting blockchain."""

    def __init__(
        self,
        index: int,
        votes: List[Dict],
        previous_hash: str,
        timestamp: Optional[str] = None,
    ):
        self.index = index
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.votes = votes
        self.previous_hash = previous_hash
        self.merkle_root = MerkleTree.compute_root(
            [json.dumps(v, sort_keys=True) for v in votes]
        )
        self.nonce = 0
        self.validator_signatures: List[str] = []
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "votes": self.votes,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "votes": self.votes,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "hash": self.hash,
            "validator_signatures": self.validator_signatures,
            "vote_count": len(self.votes),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Block":
        block = cls(
            index=data["index"],
            votes=data["votes"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
        )
        block.nonce = data.get("nonce", 0)
        block.validator_signatures = data.get("validator_signatures", [])
        block.hash = data.get("hash", block.compute_hash())
        return block


class VotingBlockchain:
    """
    Simulated Hyperledger Fabric blockchain for vote storage.
    Features:
      - PBFT consensus (simulated with validator signatures)
      - Merkle tree integrity
      - Chaincode functions
      - Chain validation
    """

    def __init__(self, election_id: str, votes_per_block: int = 10):
        self.election_id = election_id
        self.votes_per_block = votes_per_block
        self.chain: List[Block] = []
        self.pending_votes: List[Dict] = []
        self.used_tokens: set = set()
        self.receipt_index: Dict[str, int] = {}  # receipt_hash -> block_index
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(
            index=0,
            votes=[],
            previous_hash="0" * 64,
            timestamp=datetime.utcnow().isoformat(),
        )
        genesis.validator_signatures = [
            hashlib.sha256(f"validator_{i}_genesis".encode()).hexdigest()
            for i in range(3)
        ]
        self.chain.append(genesis)

    def submit_vote(self, vote_data: Dict) -> Dict:
        """
        Chaincode: submitVote
        Validates token, appends vote, creates block if threshold reached.
        Returns receipt info.
        """
        token_sig = vote_data.get("token_signature", "")
        if token_sig in self.used_tokens:
            raise ValueError("TOKEN_ALREADY_USED: Double voting attempt detected")

        self.used_tokens.add(token_sig)
        self.pending_votes.append(vote_data)

        block_info = None
        if len(self.pending_votes) >= self.votes_per_block:
            block_info = self._create_block()

        if block_info is None:
            # Vote is pending, will be included in next block
            return {
                "status": "pending",
                "receipt_hash": vote_data.get("receipt_hash", ""),
                "pending_count": len(self.pending_votes),
            }

        return block_info

    def force_create_block(self) -> Optional[Dict]:
        """Force creation of a block with pending votes (used during tallying)."""
        if self.pending_votes:
            return self._create_block()
        return None

    def _create_block(self) -> Dict:
        """Create a new block with pending votes."""
        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            votes=list(self.pending_votes),
            previous_hash=previous_block.hash,
        )

        # Simulate PBFT consensus (3 validators sign)
        new_block.validator_signatures = self._pbft_consensus(new_block)
        new_block.hash = new_block.compute_hash()

        self.chain.append(new_block)

        # Index receipts
        for vote in self.pending_votes:
            receipt = vote.get("receipt_hash", "")
            if receipt:
                self.receipt_index[receipt] = new_block.index

        self.pending_votes = []

        return {
            "status": "committed",
            "block_index": new_block.index,
            "block_hash": new_block.hash,
            "merkle_root": new_block.merkle_root,
            "vote_count": len(new_block.votes),
        }

    def _pbft_consensus(self, block: Block) -> List[str]:
        """
        Simulate PBFT consensus.
        In production: peer nodes validate and sign the block.
        Here: 3 simulated validators check block integrity and sign.
        """
        signatures = []
        for i in range(3):
            # Each validator independently computes and signs block hash
            validator_data = f"validator_{i}|{block.compute_hash()}|{block.merkle_root}"
            sig = hashlib.sha256(validator_data.encode()).hexdigest()
            signatures.append(sig)
        return signatures

    def query_vote(self, receipt_hash: str) -> Optional[Dict]:
        """Chaincode: queryVote - Look up a vote by receipt hash."""
        block_idx = self.receipt_index.get(receipt_hash)
        if block_idx is None:
            # Check pending votes
            for vote in self.pending_votes:
                if vote.get("receipt_hash") == receipt_hash:
                    return {
                        "found": True,
                        "status": "pending",
                        "receipt_hash": receipt_hash,
                        "block_index": None,
                        "block_hash": None,
                    }
            return None

        block = self.chain[block_idx]
        return {
            "found": True,
            "status": "committed",
            "receipt_hash": receipt_hash,
            "block_index": block.index,
            "block_hash": block.hash,
            "timestamp": block.timestamp,
        }

    def tally_votes(self) -> Dict[str, int]:
        """
        Chaincode: tallyVotes
        Count votes by candidate. In production, this uses homomorphic
        decryption on aggregated ciphertexts.
        For the simulation, we extract candidate_index from encrypted_ballot metadata.
        """
        # First, commit any pending votes
        self.force_create_block()

        tally: Dict[str, int] = {}
        for block in self.chain[1:]:  # Skip genesis
            for vote in block.votes:
                candidate_idx = vote.get("candidate_index", "unknown")
                key = str(candidate_idx)
                tally[key] = tally.get(key, 0) + 1
        return tally

    def validate_chain(self) -> bool:
        """Validate the entire blockchain integrity."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check hash linkage
            if current.previous_hash != previous.hash:
                return False

            # Check block hash integrity
            if current.hash != current.compute_hash():
                return False

            # Check Merkle root
            expected_merkle = MerkleTree.compute_root(
                [json.dumps(v, sort_keys=True) for v in current.votes]
            )
            if current.merkle_root != expected_merkle:
                return False

            # Check consensus (at least 2 of 3 validators)
            if len(current.validator_signatures) < 2:
                return False

        return True

    def get_chain_summary(self) -> Dict:
        """Get a summary of the blockchain state."""
        total_votes = sum(len(b.votes) for b in self.chain[1:])
        return {
            "election_id": self.election_id,
            "total_blocks": len(self.chain),
            "total_votes": total_votes + len(self.pending_votes),
            "committed_votes": total_votes,
            "pending_votes": len(self.pending_votes),
            "is_valid": self.validate_chain(),
            "last_block_hash": self.chain[-1].hash,
        }

    def get_all_blocks(self) -> List[Dict]:
        """Return all blocks as dictionaries."""
        return [b.to_dict() for b in self.chain]

    def to_json(self) -> str:
        """Serialize the entire blockchain to JSON."""
        return json.dumps({
            "election_id": self.election_id,
            "votes_per_block": self.votes_per_block,
            "chain": [b.to_dict() for b in self.chain],
            "pending_votes": self.pending_votes,
            "used_tokens": list(self.used_tokens),
            "receipt_index": self.receipt_index,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "VotingBlockchain":
        """Deserialize a blockchain from JSON."""
        data = json.loads(json_str)
        bc = cls.__new__(cls)
        bc.election_id = data["election_id"]
        bc.votes_per_block = data["votes_per_block"]
        bc.chain = [Block.from_dict(b) for b in data["chain"]]
        bc.pending_votes = data["pending_votes"]
        bc.used_tokens = set(data["used_tokens"])
        bc.receipt_index = data["receipt_index"]
        return bc


# ===========================================================================
# BLOCKCHAIN MANAGER (manages per-election blockchains)
# ===========================================================================

_blockchains: Dict[str, VotingBlockchain] = {}


def get_blockchain(election_id: str) -> VotingBlockchain:
    """Get or create a blockchain for an election."""
    if election_id not in _blockchains:
        _blockchains[election_id] = VotingBlockchain(election_id)
    return _blockchains[election_id]


def reset_blockchain(election_id: str):
    """Reset blockchain for an election (admin only)."""
    if election_id in _blockchains:
        del _blockchains[election_id]
