import uuid
from fastapi import FastAPI, HTTPException
from typing import List

from models import (
    ClaimInput, ClaimRecord, ReviewStatus, 
    ReviewActionRequest, OverrideCategoryRequest
)
from rules_engine import load_policy, run_deterministic_checks
from ai_agent import analyze_claim_with_policy
from database import (
    save_claim, get_all_claims, get_claim_by_id, 
    log_audit_event, get_audit_trail
)

app = FastAPI(
    title="Expense Claim Policy Review Assistant",
    description="Automated hybrid compliance reviewer combining deterministic rules and semantic policy AI.",
    version="1.0.0"
)

POLICY = load_policy("policy.json")

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Expense Claim Review Assistant", "policy_version": POLICY["policy_version"]}

@app.post("/api/claims/submit", response_model=ClaimRecord)
def submit_claim(claim: ClaimInput):
    existing = get_all_claims()
    
    # 1. Run Deterministic Checks
    det_results = run_deterministic_checks(claim, existing, POLICY)
    
    # 2. Run AI Policy Review Agent
    ai_results = analyze_claim_with_policy(claim, POLICY)
    
    # Determine initial status
    initial_status = ReviewStatus.PENDING
    if det_results.is_duplicate or not det_results.receipt_compliant or not det_results.valid_date:
        initial_status = ReviewStatus.REQUIRES_CLARIFICATION
    
    record = ClaimRecord(
        id=f"CLM-{str(uuid.uuid4())[:6].upper()}",
        claim=claim,
        status=initial_status,
        deterministic_checks=det_results,
        ai_findings=ai_results
    )
    save_claim(record)
    return record

@app.get("/api/claims", response_model=List[ClaimRecord])
def list_claims():
    return get_all_claims()

@app.get("/api/claims/{claim_id}", response_model=ClaimRecord)
def get_claim(claim_id: str):
    record = get_claim_by_id(claim_id)
    if not record:
        raise HTTPException(status_code=404, detail="Claim not found")
    return record

@app.post("/api/claims/{claim_id}/decision")
def apply_review_decision(claim_id: str, req: ReviewActionRequest):
    record = get_claim_by_id(claim_id)
    if not record:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    old_status = record.status
    record.status = req.action
    record.reviewer_notes = req.reviewer_notes
    
    log_audit_event(
        claim_id=claim_id,
        action=f"DECISION_{req.action.value}",
        actor="FINANCE_REVIEWER",
        details=f"Status changed from {old_status.value} to {req.action.value}. Notes: {req.reviewer_notes or 'None'}"
    )
    return {"success": True, "claim_id": claim_id, "new_status": record.status}

@app.post("/api/claims/{claim_id}/override")
def override_category(claim_id: str, req: OverrideCategoryRequest):
    record = get_claim_by_id(claim_id)
    if not record:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    old_cat = record.claim.category or record.ai_findings.classified_category
    record.reviewer_override_category = req.new_category
    
    log_audit_event(
        claim_id=claim_id,
        action="CATEGORY_OVERRIDE",
        actor="FINANCE_REVIEWER",
        details=f"Category manually changed from '{old_cat}' to '{req.new_category}'. Reason: {req.override_reason}"
    )
    return {"success": True, "claim_id": claim_id, "active_category": req.new_category}

@app.get("/api/claims/{claim_id}/history")
def view_audit_history(claim_id: str):
    history = get_audit_trail(claim_id)
    return {"claim_id": claim_id, "history": history}