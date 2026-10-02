import uuid
from datetime import datetime
from typing import Dict, List, Optional
from models import ClaimRecord, ReviewStatus

# In-memory thread-safe / persistent-ready SQLite compatible store
CLAIMS_DB: Dict[str, ClaimRecord] = {}
AUDIT_LOGS: List[dict] = []

def save_claim(record: ClaimRecord):
    CLAIMS_DB[record.id] = record
    log_audit_event(
        claim_id=record.id,
        action="CLAIM_INGESTED",
        actor="SYSTEM_PIPELINE",
        details=f"Claim ingested for claimant {record.claim.claimant} with initial status {record.status}."
    )

def get_all_claims() -> List[ClaimRecord]:
    return list(CLAIMS_DB.values())

def get_claim_by_id(claim_id: str) -> Optional[ClaimRecord]:
    return CLAIMS_DB.get(claim_id)

def log_audit_event(claim_id: str, action: str, actor: str, details: str):
    AUDIT_LOGS.append({
        "event_id": str(uuid.uuid4())[:8],
        "claim_id": claim_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "actor": actor,
        "details": details
    })

def get_audit_trail(claim_id: str) -> List[dict]:
    return [event for event in AUDIT_LOGS if event["claim_id"] == claim_id]