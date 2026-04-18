"""
Cryptographic Service for TN SecureVote
Implements:
  - RSA Blind Signatures (voter token issuance, identity-vote unlinking)
  - ElGamal Encryption (vote encryption with homomorphic properties)
  - SHA-256 Receipt Generation (vote verification)
  - Zero-Knowledge Proof simulation (vote validity proof)
"""
import hashlib
import json
import secrets
import base64
from typing import Tuple, Dict, Optional
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend


# ===========================================================================
# RSA BLIND SIGNATURE SERVICE
# ===========================================================================
# Protocol:
# 1. Voter generates random token T
# 2. Voter blinds T: T_blind = T * r^e mod N
# 3. Authority signs T_blind: S_blind = T_blind^d mod N (without seeing T)
# 4. Voter unblinds: S = S_blind * r^(-1) mod N
# 5. (T, S) is a valid token-signature pair, unlinkable to voter identity

class BlindSignatureService:
    """RSA Blind Signature implementation for anonymous vote token issuance."""

    def __init__(self, key_size: int = 2048):
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )
        self._public_key = self._private_key.public_key()
        pub_numbers = self._public_key.public_numbers()
        priv_numbers = self._private_key.private_numbers()
        self.n = pub_numbers.n
        self.e = pub_numbers.e
        self.d = priv_numbers.d

    def get_public_key_pem(self) -> str:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def get_public_params(self) -> Dict[str, str]:
        """Return n, e as base64 for client-side blinding."""
        return {
            "n": base64.b64encode(self.n.to_bytes((self.n.bit_length() + 7) // 8, 'big')).decode(),
            "e": base64.b64encode(self.e.to_bytes((self.e.bit_length() + 7) // 8, 'big')).decode(),
        }

    def sign_blinded_token(self, blinded_token_b64: str) -> str:
        """
        Sign a blinded token. The authority never sees the actual token.
        S_blind = T_blind^d mod N
        """
        blinded_bytes = base64.b64decode(blinded_token_b64)
        blinded_int = int.from_bytes(blinded_bytes, 'big')
        signed_int = pow(blinded_int, self.d, self.n)
        signed_bytes = signed_int.to_bytes((self.n.bit_length() + 7) // 8, 'big')
        return base64.b64encode(signed_bytes).decode()

    def verify_token_signature(self, token_b64: str, signature_b64: str) -> bool:
        """
        Verify an unblinded token-signature pair.
        Check: S^e mod N == T
        """
        try:
            token_bytes = base64.b64decode(token_b64)
            sig_bytes = base64.b64decode(signature_b64)
            token_int = int.from_bytes(token_bytes, 'big')
            sig_int = int.from_bytes(sig_bytes, 'big')
            recovered = pow(sig_int, self.e, self.n)
            return recovered == token_int
        except Exception:
            return False

    @staticmethod
    def generate_token() -> Tuple[str, str]:
        """Generate a random vote token and blinding factor (client-side simulation)."""
        token = secrets.token_bytes(32)
        token_b64 = base64.b64encode(token).decode()
        blinding_factor = secrets.token_bytes(32)
        blinding_b64 = base64.b64encode(blinding_factor).decode()
        return token_b64, blinding_b64

    def blind_token(self, token_b64: str) -> Tuple[str, int]:
        """
        Blind a token for signing (client-side simulation).
        T_blind = T * r^e mod N
        Returns (blinded_token_b64, r) where r is the blinding factor.
        """
        token_bytes = base64.b64decode(token_b64)
        token_int = int.from_bytes(token_bytes, 'big') % self.n

        # Generate random blinding factor r, coprime to N
        while True:
            r = secrets.randbelow(self.n - 2) + 2
            try:
                pow(r, -1, self.n)
                break
            except ValueError:
                continue

        # T_blind = T * r^e mod N
        r_e = pow(r, self.e, self.n)
        blinded = (token_int * r_e) % self.n
        blinded_bytes = blinded.to_bytes((self.n.bit_length() + 7) // 8, 'big')
        return base64.b64encode(blinded_bytes).decode(), r

    def unblind_signature(self, signed_blinded_b64: str, r: int) -> str:
        """
        Unblind the signed token (client-side simulation).
        S = S_blind * r^(-1) mod N
        """
        signed_bytes = base64.b64decode(signed_blinded_b64)
        signed_int = int.from_bytes(signed_bytes, 'big')
        r_inv = pow(r, -1, self.n)
        unblinded = (signed_int * r_inv) % self.n
        unblinded_bytes = unblinded.to_bytes((self.n.bit_length() + 7) // 8, 'big')
        return base64.b64encode(unblinded_bytes).decode()


# ===========================================================================
# ELGAMAL ENCRYPTION SERVICE
# ===========================================================================
# Simplified ElGamal over integers for vote encryption.
# In production, this would use elliptic curves (e.g., Curve25519).
# Supports additive homomorphism for tallying.

class ElGamalService:
    """ElGamal encryption for vote ballots with homomorphic tallying support."""

    def __init__(self):
        # Use a safe prime for the group
        # In production, use standardized parameters (RFC 3526)
        self.p = int(
            "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
            "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
            "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
            "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
            "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381"
            "FFFFFFFFFFFFFFFF", 16
        )
        self.g = 2
        # Generate election key pair
        self.private_key = secrets.randbelow(self.p - 2) + 1
        self.public_key = pow(self.g, self.private_key, self.p)

    def get_public_params(self) -> Dict[str, str]:
        """Return public parameters for client-side encryption."""
        return {
            "p": base64.b64encode(self.p.to_bytes((self.p.bit_length() + 7) // 8, 'big')).decode(),
            "g": str(self.g),
            "public_key": base64.b64encode(
                self.public_key.to_bytes((self.public_key.bit_length() + 7) // 8, 'big')
            ).decode(),
        }

    def encrypt(self, vote_value: int) -> Dict[str, str]:
        """
        Encrypt a vote using ElGamal.
        Encode vote as g^vote for additive homomorphism.
        (c1, c2) = (g^r mod p, g^vote * pk^r mod p)
        """
        r = secrets.randbelow(self.p - 2) + 1
        c1 = pow(self.g, r, self.p)
        g_vote = pow(self.g, vote_value, self.p)
        c2 = (g_vote * pow(self.public_key, r, self.p)) % self.p
        return {
            "c1": base64.b64encode(c1.to_bytes((self.p.bit_length() + 7) // 8, 'big')).decode(),
            "c2": base64.b64encode(c2.to_bytes((self.p.bit_length() + 7) // 8, 'big')).decode(),
        }

    def decrypt(self, ciphertext: Dict[str, str]) -> int:
        """
        Decrypt an ElGamal ciphertext.
        m = c2 * c1^(-sk) mod p = g^vote
        Then find vote by brute-force discrete log (feasible for small vote values).
        """
        c1 = int.from_bytes(base64.b64decode(ciphertext["c1"]), 'big')
        c2 = int.from_bytes(base64.b64decode(ciphertext["c2"]), 'big')
        s = pow(c1, self.private_key, self.p)
        s_inv = pow(s, -1, self.p)
        g_vote = (c2 * s_inv) % self.p

        # Brute-force discrete log for small values (candidate indices 0-99)
        for i in range(100):
            if pow(self.g, i, self.p) == g_vote:
                return i
        return -1

    def homomorphic_add(self, ciphertexts: list) -> Dict[str, str]:
        """
        Homomorphically add encrypted votes.
        Product of ciphertexts = encryption of sum of plaintexts.
        """
        if not ciphertexts:
            return {"c1": "", "c2": ""}

        c1_product = 1
        c2_product = 1
        for ct in ciphertexts:
            c1 = int.from_bytes(base64.b64decode(ct["c1"]), 'big')
            c2 = int.from_bytes(base64.b64decode(ct["c2"]), 'big')
            c1_product = (c1_product * c1) % self.p
            c2_product = (c2_product * c2) % self.p

        return {
            "c1": base64.b64encode(c1_product.to_bytes((self.p.bit_length() + 7) // 8, 'big')).decode(),
            "c2": base64.b64encode(c2_product.to_bytes((self.p.bit_length() + 7) // 8, 'big')).decode(),
        }


# ===========================================================================
# RECEIPT AND HASH SERVICE
# ===========================================================================

class ReceiptService:
    """SHA-256 based vote receipt generation and verification."""

    @staticmethod
    def generate_receipt(
        token_signature: str,
        encrypted_ballot: str,
        timestamp: str,
        block_hash: str = "",
    ) -> str:
        """
        Generate a vote receipt hash.
        receipt = SHA-256(token_sig || encrypted_vote || timestamp || block_hash)
        """
        data = f"{token_signature}|{encrypted_ballot}|{timestamp}|{block_hash}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def hash_data(data: str) -> str:
        """Generic SHA-256 hash."""
        return hashlib.sha256(data.encode()).hexdigest()


# ===========================================================================
# ZKP SERVICE (Simplified Sigma Protocol)
# ===========================================================================

class ZKPService:
    """
    Zero-Knowledge Proof for vote validity.
    Proves: "My vote encodes exactly one valid candidate index"
    Without revealing: which candidate was chosen.

    Uses a simplified Schnorr-like sigma protocol simulation.
    In production, use proper ZKP libraries (e.g., libsnark, bellman).
    """

    @staticmethod
    def generate_proof(vote_value: int, num_candidates: int, election_id: str) -> Dict:
        """
        Generate a ZKP that the vote is valid (encodes one of the valid candidate indices).
        """
        # Commitment
        nonce = secrets.token_hex(32)
        commitment = hashlib.sha256(f"{nonce}|{vote_value}".encode()).hexdigest()

        # Challenge (Fiat-Shamir heuristic: hash of public inputs + commitment)
        challenge_input = f"{election_id}|{num_candidates}|{commitment}"
        challenge = hashlib.sha256(challenge_input.encode()).hexdigest()

        # Response: proves knowledge without revealing vote
        response_data = f"{nonce}|{challenge}|{vote_value}"
        response = hashlib.sha256(response_data.encode()).hexdigest()

        # Range proof: vote is in [0, num_candidates)
        range_commitments = []
        for i in range(num_candidates):
            if i == vote_value:
                rc = hashlib.sha256(f"{nonce}|{i}|real".encode()).hexdigest()
            else:
                fake_nonce = secrets.token_hex(16)
                rc = hashlib.sha256(f"{fake_nonce}|{i}|sim".encode()).hexdigest()
            range_commitments.append(rc)

        return {
            "commitment": commitment,
            "challenge": challenge,
            "response": response,
            "range_commitments": range_commitments,
            "num_candidates": num_candidates,
            "nonce_hash": hashlib.sha256(nonce.encode()).hexdigest(),
        }

    @staticmethod
    def verify_proof(proof: Dict, election_id: str) -> bool:
        """
        Verify a ZKP proof.
        In this simulation, we verify structural validity.
        """
        try:
            required_fields = ["commitment", "challenge", "response", "range_commitments", "num_candidates"]
            if not all(f in proof for f in required_fields):
                return False

            # Verify challenge was derived from commitment
            challenge_input = f"{election_id}|{proof['num_candidates']}|{proof['commitment']}"
            expected_challenge = hashlib.sha256(challenge_input.encode()).hexdigest()
            if proof["challenge"] != expected_challenge:
                return False

            # Verify range commitments count matches candidate count
            if len(proof["range_commitments"]) != proof["num_candidates"]:
                return False

            return True
        except Exception:
            return False


# ===========================================================================
# SINGLETON INSTANCES (per-election in production)
# ===========================================================================

_blind_sig_service: Optional[BlindSignatureService] = None
_elgamal_service: Optional[ElGamalService] = None


def get_blind_sig_service() -> BlindSignatureService:
    global _blind_sig_service
    if _blind_sig_service is None:
        _blind_sig_service = BlindSignatureService()
    return _blind_sig_service


def get_elgamal_service() -> ElGamalService:
    global _elgamal_service
    if _elgamal_service is None:
        _elgamal_service = ElGamalService()
    return _elgamal_service


def get_receipt_service() -> ReceiptService:
    return ReceiptService()


def get_zkp_service() -> ZKPService:
    return ZKPService()
