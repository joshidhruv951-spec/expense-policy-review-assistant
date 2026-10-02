import json
from models import ClaimInput, AIFinding

# Semantic keyword mappings for deterministic fallback / local simulation
CATEGORY_KEYWORDS = {
    "Meals & Entertainment": ["lunch", "dinner", "breakfast", "coffee", "restaurant", "client food", "meal", "drinks"],
    "Travel & Transport": ["uber", "lyft", "taxi", "flight", "cab", "metro", "train", "airline", "fare", "parking"],
    "Accommodation": ["hotel", "airbnb", "lodging", "stay", "room night"],
    "Office Supplies & Subscriptions": ["software", "github", "aws", "notebook", "monitor", "keyboard", "cable", "stationery"]
}

def analyze_claim_with_policy(claim: ClaimInput, policy: dict) -> AIFinding:
    """
    AI Agent analyzer: Classifies category, checks policy clauses, evaluates uncertainty,
    and extracts evidence citations.
    """
    desc_lower = claim.description.lower()
    cat_rules = policy["rules"]["category_limits"]
    
    # 1. Category Classification & Confidence Evaluation
    classified_cat = claim.category
    confidence = 0.95
    is_uncertain = False
    
    if not classified_cat or classified_cat not in cat_rules:
        # Infer category based on semantics
        matched_category = None
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in desc_lower for kw in keywords):
                matched_category = category
                break
        
        if matched_category:
            classified_cat = matched_category
            confidence = 0.85
        else:
            classified_cat = "Office Supplies & Subscriptions"
            confidence = 0.40
            is_uncertain = True

    # Check for short or vague descriptions
    missing_info = None
    if len(claim.description.strip().split()) < 3:
        confidence = min(confidence, 0.45)
        is_uncertain = True
        missing_info = "Specific business purpose and list of attendees/items purchased."

    # 2. Extract policy clause & citation
    section_info = cat_rules.get(classified_cat, {
        "policy_section": "General Corporate Governance",
        "description": "Standard business expenses must be clearly substantiated."
    })
    policy_section = section_info["policy_section"]
    citation_text = section_info["description"]

    # 3. Compliance reasoning
    reasons = []
    if claim.amount > section_info.get("max_amount_per_claim", 1000.0):
        reasons.append(f"Expense exceeds ${section_info['max_amount_per_claim']} policy ceiling.")
    else:
        reasons.append(f"Expense amount is within permissible ${section_info.get('max_amount_per_claim')} allocation.")
    
    if not claim.receipt_available and claim.amount > policy["rules"].get("receipt_required_threshold", 25.0):
        reasons.append("Non-compliant due to lack of verifiable proof of purchase.")

    reasoning_summary = f"Claim evaluated under {policy_section}. " + " ".join(reasons)

    return AIFinding(
        classified_category=classified_cat,
        confidence_score=round(confidence, 2),
        is_uncertain=is_uncertain,
        policy_section=policy_section,
        evidence_citation=citation_text,
        compliance_reasoning=reasoning_summary,
        missing_info_needed=missing_info
    )