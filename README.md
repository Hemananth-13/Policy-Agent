# Insurance Policy Generation Agent

An autonomous AI agent that accepts a natural language insurance request, plans its own execution steps, generates a complete professional insurance policy document, and performs a self-check on its output.

Built with **FastAPI**, **Groq (LLaMA 3.3 70B)**, and **python-docx**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Agent Workflow](#agent-workflow)
- [Policy Document Structure](#policy-document-structure)
- [Guardrails](#guardrails)
- [Engineering Improvement — Reflection](#engineering-improvement--reflection)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Sample Inputs](#sample-inputs)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Error Handling](#error-handling)
- [Design Decisions and Tradeoffs](#design-decisions-and-tradeoffs)

---

## Overview

This project implements an autonomous AI agent that:

1. Accepts a free-text insurance request from the user
2. Extracts structured applicant details from the request
3. Uses a fixed 9-task execution plan covering all required policy sections
4. Executes each task by calling a Groq-hosted LLM to write formal legal policy content
5. Reflects on the output to check completeness and flag improvements
6. Generates a professionally formatted `.docx` Word document containing only the policy

The agent is exposed via a **FastAPI REST API** (`POST /agent`) and also runnable directly from the **CLI** via `run.py`.

---

## Features

- Single-command CLI runner with live spinner animation
- Full FastAPI REST API with Swagger UI at `/docs`
- Generates a clean `.docx` insurance policy document with only the 9 policy sections — no agent internals in the output
- All 9 standard insurance policy sections generated autonomously
- Reflection / self-check after generation with fallback if rate limited
- Two-layer guardrails — code layer and LLM prompt layer
- Retry logic with exponential backoff for rate-limited LLM calls (429/503)
- Configurable model and CORS origins via environment variables
- Path traversal protection on the file download endpoint
- Custom exception hierarchy (`AgentError`, `LLMError`, `DocumentError`) for precise API error responses
- Token usage logged at DEBUG level
- API key validated at startup with a clear error message

---

## Architecture

```
run.py                  CLI entry point — spinner animation, calls agent directly
main.py                 FastAPI app — POST /agent, GET /download, GET /health
agent.py                Core agent loop — 4 steps: extract, plan, execute, reflect
groq_client.py          Groq LLM wrapper — loads system prompt, handles SSL, logs tokens
document_generator.py   Builds the .docx Word policy document
guardrails.py           Input validation — length, topic, injection, sensitive data
models.py               Pydantic models + custom exception hierarchy
prompts/
  system_prompt.md      LLM system prompt — loaded once at runtime
generated_docs/         Output .docx files (gitignored)
```

---

## Agent Workflow

```
User Input (run.py or POST /agent)
        │
        ▼
  Guardrails — code layer (guardrails.py)
  ┌─────────────────────────────────────┐
  │  Prompt injection check             │
  │  Blocked topics check               │
  │  Sensitive data check               │
  │  Length check (10–2000 chars)       │
  │  Insurance relevance check          │
  └─────────────────────────────────────┘
        │
        ▼
  Step 1 — extract_policy_details()
        Parses applicant name, age, occupation, risk factors,
        coverage type, assumptions into structured labeled fields
        │
        ▼
  Step 2 — plan_tasks()
        Returns 9 fixed tasks — no LLM call, deterministic section names
        │
        ▼
  Step 3 — execute_tasks()
        LLM writes each section as formal legal policy text:
        1. Declarations Page
        2. Insuring Agreement
        3. Risk Assessment and Underwriting Summary
        4. Coverage Details
        5. Premium Schedule
        6. Policy Conditions
        7. Exclusions
        8. Riders and Endorsements
        9. Definitions
        │
        ▼
  Step 4 — reflect()
        LLM reviews section completeness, flags gaps,
        suggests improvements — with fallback if rate limited
        │
        ▼
  document_generator.py
        Builds .docx — cover page + 9 policy sections only
        │
        ▼
  insurance_policy_TIMESTAMP_UUID.docx
```

---

## Policy Document Structure

Every generated document contains exactly:

| # | Section | Content |
|---|---|---|
| Cover | Cover Page | Insurer name, address, date issued |
| 1 | Declarations Page | Policy number, policyholder, coverage limits, premium, beneficiary |
| 2 | Insuring Agreement | Formal promise to pay benefits upon covered event |
| 3 | Risk Assessment and Underwriting Summary | Risk profile, rating, premium impact |
| 4 | Coverage Details | Benefit limits, deductibles, coinsurance, in/out-of-network |
| 5 | Premium Schedule | Base rate, rating factors, discounts, final annual/monthly premium |
| 6 | Policy Conditions | Grace period, incontestability, reinstatement, free look, renewal |
| 7 | Exclusions | Pre-existing conditions, experimental treatments, cosmetic, war, etc. |
| 8 | Riders and Endorsements | Add-ons requested (dental, vision, waiver of premium, etc.) |
| 9 | Definitions | Legal definitions of all key terms used in the policy |

---

## Guardrails

Two-layer protection against misuse and invalid input:

### Layer 1 — Code (`guardrails.py`)

Security checks run first and fail fast:

| Check | Description |
|---|---|
| Prompt injection | Blocks phrases like `ignore previous instructions`, `you are now`, `act as` |
| Blocked topics | Blocks fraud, illegal activity, hacking, terrorism, money laundering, scams |
| Sensitive data | Blocks real SSNs, credit card numbers, phone numbers, email addresses |
| Length | Rejects requests under 10 or over 2000 characters |
| Insurance relevance | Requires at least one insurance-related keyword or intent phrase |

### Layer 2 — Prompt (`prompts/system_prompt.md`)

Enforced by the LLM itself:

- Refuses off-topic requests with a defined fallback response
- Refuses fraud or illegal content
- On prompt injection: outputs `"Invalid request."` and stops immediately
- No hallucinated legal advice
- Writes only policy document text — no explanations, introductions, or commentary
- Consistent insurer name (`SecureHealth Insurance Co.`) throughout all sections

---

## Engineering Improvement — Reflection

After all 9 sections are generated, the agent makes one final LLM call to review the completed policy against the original request. It checks:

- Are all 9 required sections present?
- Are there any gaps based on the user's specific request?
- What improvements would make the policy more complete?

The reflection result (`passed`, `issues_found`, `improvements_made`) is returned in the API response. If the daily token limit is exhausted, a fallback reflection is generated automatically based on task completion status — the agent never crashes.

This closes the autonomous agent loop with self-evaluation.

---

## Project Structure

```
Flud Ai/
├── agent.py                 Core agent loop (extract, plan, execute, reflect)
├── document_generator.py    Word document builder — 9 sections only
├── groq_client.py           Groq LLM wrapper with SSL fix and token logging
├── guardrails.py            Input validation — 5 checks across 2 categories
├── main.py                  FastAPI application
├── models.py                Pydantic models + AgentError, LLMError, DocumentError
├── run.py                   CLI runner with spinner animation
├── setup.py                 Automated setup script
├── requirements.txt         Pinned Python dependencies
├── sample_inputs.txt        Ready-to-use test cases (standard + complex)
├── .env.example             Environment variable template
├── .gitignore               Excludes .env, generated_docs/, __pycache__/
├── prompts/
│   └── system_prompt.md     LLM system prompt loaded at runtime
└── generated_docs/          Output .docx files (gitignored)
```

---

## Setup

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Hemananth-13/Policy-Agent.git
cd Policy-Agent

# 2. Run the automated setup script
python setup.py

# 3. Add your Groq API key to .env
#    Get a free key at https://console.groq.com
#    Edit .env and set: GROQ_API_KEY=your_key_here

# 4. Activate the virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 5. Run
python run.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for a detailed step-by-step guide including troubleshooting.

---

## Usage

### Option 1 — CLI (recommended)

```bash
python run.py
```

The terminal shows a live spinner with stage labels:
```
  ⠹  Analysing request       ...
  ⠸  Planning policy sections...
  ⠼  Writing policy content  ...
  ⠴  Running quality check   ...
  [OK]  Document ready
```

After completion, the policy sections and quality check results are printed and the `.docx` is saved to the project folder.

### Option 2 — API

Start the server:

```bash
uvicorn main:app --reload
```

Send a request:

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d "{\"request\": \"Generate a health insurance policy for a 30-year-old male software engineer.\"}"
```

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health` (also verifies Groq connectivity)

---

## Sample Inputs

Saved in `sample_inputs.txt`. Copy each as a single line into the terminal prompt.

**Test Case 1 — Standard:**
```
Generate a health insurance policy for a 30-year-old male, non-smoker, no pre-existing conditions, working as a software engineer, looking for individual coverage with dental and vision add-ons.
```

**Test Case 2 — Complex / Ambiguous:**
```
I need an insurance policy for a 45-year-old female who smokes occasionally, has been diagnosed with type 2 diabetes for 3 years and takes metformin daily, and runs a small home-based bakery business with two part-time employees and commercial-grade kitchen equipment worth around $15,000. She owns her home valued at approximately $320,000 with a mortgage, has a 16-year-old dependent child, and her husband passed away two years ago. She wants health coverage for herself including dental and vision, property coverage for both her home and the business equipment inside it, and is unsure whether to add life insurance given her dependent child but is worried about the higher premium. She has not decided on a deductible amount, does not know whether to go with a PPO or HMO, and is open to suggestions on riders. Her annual income from the bakery is roughly $48,000 and she has no other insurance currently.
```

The complex case forces the agent to handle multiple policy types, ambiguous inputs, missing information, and make clearly stated assumptions.

---

## API Reference

### `POST /agent`

Generates an insurance policy document.

**Request body:**
```json
{
  "request": "Generate a health insurance policy for..."
}
```

**Response:**
```json
{
  "request": "...",
  "tasks": [
    { "task_id": 1, "task_name": "Declarations Page", "status": "completed" },
    { "task_id": 2, "task_name": "Insuring Agreement", "status": "completed" }
  ],
  "reflection": {
    "passed": true,
    "issues_found": [],
    "improvements_made": []
  },
  "document_path": "insurance_policy_20240101_120000_abc12345.docx",
  "download_url": "/download?filename=insurance_policy_20240101_120000_abc12345.docx",
  "message": "Insurance policy generated successfully."
}
```

### `GET /download?filename=<filename>`

Downloads a generated `.docx` file. Filename must resolve within `generated_docs/` — path traversal attempts return 400.

### `GET /health`

Returns app status and verifies Groq LLM connectivity.

```json
{
  "status": "healthy",
  "llm": "connected",
  "model": "llama-3.3-70b-versatile"
}
```

---

## Error Handling

| HTTP Code | Exception | Cause |
|---|---|---|
| 400 | — | Empty request body |
| 422 | `GuardrailError` | Input blocked by guardrails |
| 400 | — | Path traversal attempt on `/download` |
| 502 | `LLMError` | Groq API call failed after all retries |
| 500 | `DocumentError` | Failed to save the `.docx` file |
| 500 | `AgentError` | Agent loop failure |
| 504 | `asyncio.TimeoutError` | Agent exceeded 300 second timeout |

CLI exit codes: `0` = success, `1` = system error, `2` = guardrail blocked.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Your Groq API key. Get one free at [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Comma-separated list of allowed CORS origins |

---

## Design Decisions and Tradeoffs

### Fixed Task Plan vs LLM-Generated Tasks

The 9 policy section names are hardcoded in `plan_tasks()` rather than generated by the LLM. Early versions asked the LLM to generate task names, which produced verbose descriptions that leaked into the document output and caused inconsistent section headings. Fixed names give clean, consistent headings every run and eliminate one LLM call.

### Autonomous Planning vs Deterministic Workflow

The agent uses a deterministic 9-task structure (ensuring all required sections are always present) while keeping the content of each section fully autonomous — the LLM decides what to write based on the applicant's profile. This balances reliability with genuine autonomous reasoning and makes the output predictable.

### Reflection as Self-Check vs Multi-Agent Validation

Rather than a separate validator agent, a single reflection call at the end reviews the agent's own output. This keeps the system simple, reduces token usage, and is sufficient for the scope of this use case. A graceful fallback is in place when the daily token limit is hit.

### Single LLM Provider

The system uses Groq's free tier (`llama-3.3-70b-versatile`) which provides 100,000 tokens/day at no cost. Each full policy run uses approximately 10,000–15,000 tokens. The model is configurable via `GROQ_MODEL` in `.env` for easy switching.
