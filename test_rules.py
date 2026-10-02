import pytest
from datetime import date, timedelta
from models import ClaimInput, ClaimRecord, ReviewStatus, DeterministicCheckResult, AIFinding
from rules_engine import run_deterministic_checks, load_policy
from ai_agent import analyze_claim_with_policy

@pytest.fixture
def policy():
    return load_policy("policy.json")

def test_missing_receipt_above_threshold(policy):
    claim = ClaimInput(
        claimant="Jane Doe",
        date=date.today() - timedelta(days=5),
        category="Meals & Entertainment",
        amount=65.0,
        currency="USD",
        description="Dinner with partners",
        receipt_available=False
    )
    res = run_deterministic_checks(claim, [], policy)
    assert res.receipt_compliant is False
    assert any("Missing mandatory receipt" in v for v in res.rule_violations)

def test_category_limit_exceeded(policy):
    claim = ClaimInput(
        claimant="John Smith",
        date=date.today() - timedelta(days=2),
        category="Meals & Entertainment",
        amount=150.0,
        currency="USD",
        description="Expensive dinner",
        receipt_available=True
    )
    res = run_deterministic_checks(claim, [], policy)
    assert res.within_limit is False
    assert any("exceeds category maximum" in v for v in res.rule_violations)

def test_duplicate_detection(policy):
    existing_claim = ClaimRecord(
        id="CLM-001",
        claim=ClaimInput(
            claimant="Alice",
            date=date(2026, 9, 20),
            category="Travel & Transport",
            amount=35.0,
            currency="USD",
            description="Taxi to airport",
            receipt_available=True
        ),
        status=ReviewStatus.PENDING,
        deterministic_checks=DeterministicCheckResult(),
        ai_findings=AIFinding(
            classified_category="Travel & Transport",
            confidence_score=0.9,
            is_uncertain=False,
            policy_section="Section 3.2",
            evidence_citation="",
            compliance_reasoning=""
        )
    )
    
    new_claim = ClaimInput(
        claimant="Alice",
        date=date(2026, 9, 20),
        category="Travel & Transport",
        amount=35.0,
        currency="USD",
        description="Taxi ride to terminal",
        receipt_available=True
    )
    
    res = run_deterministic_checks(new_claim, [existing_claim], policy)
    assert res.is_duplicate is True
    assert res.duplicate_of_id == "CLM-001"

def test_future_date_rejected(policy):
    claim = ClaimInput(
        claimant="Bob",
        date=date.today() + timedelta(days=3),
        category="Accommodation",
        amount=120.0,
        currency="USD",
        description="Future stay",
        receipt_available=True
    )
    res = run_deterministic_checks(claim, [], policy)
    assert res.valid_date is False

def test_ai_agent_semantic_classification_and_uncertainty(policy):
    # Ambiguous claim with short description
    claim = ClaimInput(
        claimant="Carol",
        date=date.today() - timedelta(days=1),
        category=None,
        amount=40.0,
        currency="USD",
        description="stuff",
        receipt_available=True
    )
    ai_finding = analyze_claim_with_policy(claim, policy)
    assert ai_finding.is_uncertain is True
    assert ai_finding.missing_info_needed is not None