from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_CLARIFICATION = "REQUIRES_CLARIFICATION"

class ClaimInput(BaseModel):
    claimant: str = Field(..., description="Name of claimant")
    date: datetime.date = Field(..., description="Expense date")
    category: Optional[str] = Field(None, description="Expense category")
    amount: float = Field(..., gt=0, description="Amount")
    currency: str = Field(default="USD", description="Currency code")
    description: str = Field(..., min_length=3, description="Claim description")
    receipt_available: bool = Field(..., description="Whether receipt is provided")

class DeterministicCheckResult(BaseModel):
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    receipt_compliant: bool = True
    within_limit: bool = True
    limit_amount: Optional[float] = None
    valid_date: bool = True
    rule_violations: List[str] = []

class AIFinding(BaseModel):
    classified_category: str
    confidence_score: float
    is_uncertain: bool
    policy_section: str
    evidence_citation: str
    compliance_reasoning: str
    missing_info_needed: Optional[str] = None

class ClaimRecord(BaseModel):
    id: str
    claim: ClaimInput
    status: ReviewStatus = ReviewStatus.PENDING
    deterministic_checks: DeterministicCheckResult
    ai_findings: AIFinding
    reviewer_override_category: Optional[str] = None
    reviewer_notes: Optional[str] = None

class ReviewActionRequest(BaseModel):
    action: ReviewStatus
    reviewer_notes: Optional[str] = None

class OverrideCategoryRequest(BaseModel):
    new_category: str
    override_reason: str