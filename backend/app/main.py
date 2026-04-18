"""
TN SecureVote - Main FastAPI Application
Secure Online Voting System for Tamil Nadu
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, vote, audit, election, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and demo data on startup."""
    init_db()

    # Auto-setup demo if demo mode is enabled
    if settings.DEMO_MODE:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            from app.routers.demo import setup_demo
            setup_demo(db)
        except Exception as e:
            print(f"Demo setup note: {e}")
        finally:
            db.close()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "🗳️ TN SecureVote — Secure Online Voting System for Tamil Nadu\n\n"
        "End-to-end verifiable, blockchain-backed, cryptographically secure.\n"
        "Supports Tamil + English bilingual interface.\n\n"
        "**Security Features:**\n"
        "- RSA Blind Signatures (anonymous vote tokens)\n"
        "- ElGamal Encryption (homomorphic tallying)\n"
        "- Zero-Knowledge Proofs (vote validity)\n"
        "- Blockchain (tamper-proof storage)\n"
        "- SHA-256 Receipts (voter verification)\n"
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(vote.router)
app.include_router(audit.router)
app.include_router(election.router)
app.include_router(demo.router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "demo_mode": settings.DEMO_MODE,
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/auth",
            "vote": "/api/vote",
            "audit": "/api/audit",
            "election": "/api/election",
            "demo": "/api/demo",
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.APP_NAME}
