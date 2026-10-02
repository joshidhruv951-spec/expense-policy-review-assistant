import json
from datetime import date, datetime
from typing import List, Tuple
from models import ClaimInput, DeterministicCheckResult, ClaimRecord

def load_policy(filepath: str = "policy.json") -> dict:
    with open(filepath, "r") as f:
        return json.load(f)

def run_deterministic_checks(
    new_claim: ClaimInput, 
    existing_claims: List[ClaimRecord], 
    policy: dict
) -> DeterministicCheckResult:
    violations = []
    
    # 1. Duplicate detection (exact claimant, date, amount)
    is_dup = False
    dup_id = None
    for rec in existing_claims:
        if (rec.claim.claimant.strip().lower() == new_claim.claimant.strip().lower() and
            rec.claim.date == new_claim.date and
            abs(rec.claim.amount - new_claim.amount) < 0.001):
            is_dup = True
            dup_id = rec.id
            violations.append(f"Potential duplicate claim detected. Matches Claim ID: {dup_id}")
            break

    # 2. Date validation (future date or stale > 90 days)
    today = date.today()
    valid_date = True
    if new_claim.date > today:
        valid_date = False
        violations.append(f"Invalid claim date: {new_claim.date} is in the future.")
    
    max_days = policy["rules"].get("max_claim_age_days", 90)
    age_days = (today - new_claim.date).days
    if age_days > max_days:
        valid_date = False
        violations.append(f"Claim is stale: submitted {age_days} days after expense (policy limit {max_days} days).")

    # 3. Receipt verification
    receipt_threshold = policy["rules"].get("receipt_required_threshold", 25.0)
    receipt_compliant = True
    if new_claim.amount >= receipt_threshold and not new_claim.receipt_available:
        receipt_compliant = False
        violations.append(f"Missing mandatory receipt: Claim amount ${new_claim.amount:.2f} exceeds ${receipt_threshold:.2f} threshold.")

    # 4. Configured Category limits
    within_limit = True
    cat_limit = None
    cat_rules = policy["rules"]["category_limits"]
    if new_claim.category and new_claim.category in cat_rules:
        cat_limit = cat_rules[new_claim.category]["max_amount_per_claim"]
        if new_claim.amount > cat_limit:
            within_limit = False
            violations.append(f"Amount ${new_claim.amount:.2f} exceeds category maximum of ${cat_limit:.2f} for '{new_claim.category}'.")

    return DeterministicCheckResult(
        is_duplicate=is_dup,
        duplicate_of_id=dup_id,
        receipt_compliant=receipt_compliant,
        within_limit=within_limit,
        limit_amount=cat_limit,
        valid_date=valid_date,
        rule_violations=violations
    )