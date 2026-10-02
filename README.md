# Expense Claim Policy Review Assistant

An intelligent, hybrid expense compliance review system that pairs strict deterministic rule validation with LLM-powered semantic policy analysis. Designed for corporate finance teams to audit employee claims, flag policy discrepancies, manage reviewer workflows, and track immutable audit histories.

---

## Key Features

- **Deterministic Rule Engine (Zero-Latency Validation)**
  - Exact duplicate claim detection (matches `claimant`, `date`, and `amount`).
  - Hard budget and category ceiling verification (Meals, Travel, Accommodation, Supplies).
  - Mandatory receipt requirement enforcement based on expense thresholds.
  - Strict date validation (rejects future dates and stale claims > 90 days).
  - Mandatory field schema enforcement via Pydantic.

- **AI Policy Review Agent (LLM + Structured Findings)**
  - Semantic category classification for ambiguous expense descriptions.
  - Policy section matching with direct evidentiary citations.
  - Explicit uncertainty flagging for ambiguous, borderline, or low-confidence claims.
  - Automated missing information request generation.

- **Reviewer-in-the-Loop Workbench**
  - Claim decision actions: **Approve**, **Reject**, or **Request Clarification**.
  - Manual override mechanism allowing human reviewers to modify AI classifications with logged justification.
  - Full, tamper-evident decision audit log tracking timestamps, actors, and rationale.

---

## System Architecture

```text
       [Employee Claim Submission / JSON Batch]
                          │
                          ▼
           [Pydantic Schema Validation]
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
 [Deterministic Engine]          [AI Policy Agent]
 - Duplicate Detection           - Semantic Categorization
 - Receipt Compliance Check      - Policy Clause Citation
 - Category Budget Limits        - Uncertainty Detection
          │                               │
          └───────────────┬───────────────┘
                          ▼
             [Reviewer Decision Workbench]
      - Human Verification / Override
      - Actions: Approve / Reject / Clarify
                          │
                          ▼
        [SQLite Database & Audit Trail Log]
```

---

## Project Structure

```text
├── policy.json              # Configurable organizational expense rules & thresholds
├── main.py                  # FastAPI application endpoints & routing
├── models.py                # Pydantic schemas (Claim, Policy, ReviewDecision, Audit)
├── rules_engine.py          # Deterministic business logic & duplicate checking
├── ai_agent.py              # LLM policy citation, classification & reasoning
├── database.py              # SQLite storage & decision history ledger
├── test_rules.py            # Comprehensive Pytest suite for business rules
├── requirements.txt         # Core dependencies
└── README.md                # Project documentation
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- An OpenAI or Gemini API key (optional for running deterministic tests; mock fallback included)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/expense-policy-review-assistant.git
   cd expense-policy-review-assistant
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_api_key_here
   # Or set MOCK_AI=True to test the full pipeline offline without API calls
   MOCK_AI=True
   ```

---

## Running the Application

### 1. Launch the FastAPI Server
```bash
uvicorn main:app --reload --port 8000
```
Access the interactive Swagger API documentation at:
`http://localhost:8000/docs`

### 2. Run Test Suite
Execute the deterministic rule validation and duplicate detection tests:
```bash
pytest test_rules.py -v
```

---

## API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/claims/submit` | Ingests a new claim and runs deterministic & AI checks |
| `GET` | `/api/claims/pending` | Lists all claims awaiting human reviewer triage |
| `POST` | `/api/claims/{claim_id}/decision` | Reviewer action (`APPROVE`, `REJECT`, `REQUEST_CLARIFICATION`) |
| `POST` | `/api/claims/{claim_id}/override` | Reviewer category override with required justification |
| `GET` | `/api/claims/{claim_id}/history` | Retrieves complete audit history and decision timestamps |

---

## Scope & Non-Requirements
Per design scope, this project focuses strictly on compliance auditing and reviewer workflow. It intentionally does not implement:
- Actual payment processing or bank transfers
- Payroll integration
- Tax advisory calculations
- Raw receipt image OCR extraction