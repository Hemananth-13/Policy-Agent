# Insurance Policy Generation Agent

An autonomous AI agent that accepts a natural language insurance request, plans its own execution steps, generates a complete professional insurance policy document, and performs a self-check on its output.

Built with **FastAPI**, **Groq (LLaMA 3.3 70B)**, and **python-docx**.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Agent Workflow](#agent-workflow)
- [Guardrails](#guardrails)
- [Engineering Improvement](#engineering-improvement)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Sample Inputs](#sample-inputs)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Design Decisions & Tradeoffs](#design-decisions--tradeoffs)

---

## Overview

This project implements an autonomous AI agent that:

1. Accepts a free-text insurance request from the user
2. Extracts structured applicant details from the request
3. Plans a fixed 9-task execution plan covering all required policy sections
4. Executes each task by calling a Groq-hosted LLM to write formal policy content
5. Reflects on the output to check completeness and flag improvements
6. Generates a professionally formatted `.docx` Word document containing only the policy

The agent is exposed via a **FastAPI REST API** (`POST /agent`) and also runnable directly from the **CLI** via `run.py`.

---

## Features

- Single-command CLI runner with live spinner animation
- Full FastAPI REST API with Swagger UI at `/docs`
- Generates a clean, professional `.docx` insurance policy document
- All 9 standard insurance policy sections generated autonomously
- Reflection / self-check after generation
- Two-layer guardrails (code + LLM prompt)
- Retry logic with exponential backoff for rate-limited LLM calls
- Configurable model and CORS origins via environment variables
- Path traversal protection on file download endpoint
- Custom exception hierarchy for precise API error responses

---

## Architecture

```
run.py                  CLI entry point — spinner UI, calls agent directly
main.py                 FastAPI app — POST /agent, GET /download, GET /health
agent.py                Core agent loop — 4 steps: extract, plan, execute, reflect
groq_client.py          Groq LLM wrapper — loads system prompt, handles SSL
document_generator.py   Builds the .docx Word policy document
guardrails.py           Input validation — length, topic, injection, sensitive data
models.py               Pydantic models + custom exception hierarchy
prompts/
  system_prompt.md      LLM system prompt — loaded at runtime
generated_docs/         Output .docx files (gitignored)
```

---

## Agent Workflow

```
User Input
    │
    ▼
Guardrails (code layer)
    │  length check, topic check, injection check, sensitive data check
    ▼
Step 1 — extract_policy_details()
    │  Parses applicant profile, risk factors, assumptions into structured fields
    ▼
Step 2 — plan_tasks()
    │  Returns 9 fixed tasks (no LLM call — task names are deterministic)
    ▼
Step 3 — execute_tasks()
    │  LLM writes each of the 9 policy sections as formal legal document text:
    │    1. Declarations Page
    │    2. Insuring Agreement
    │    3. Risk Assessment and Underwriting Summary
    │    4. Coverage Details
    │    5. Premium Schedule
    │    6. Policy Conditions
    │    7. Exclusions
    │    8. Riders and Endorsements
    │    9. Definitions
    ▼
Step 4 — reflect()
    │  LLM reviews completeness, flags issues, suggests improvements
    ▼
document_generator.py
    │  Builds clean .docx with cover page + 9 sections
    ▼
insurance_policy_TIMESTAMP_UUID.docx
```

---

## Guardrails

Two-layer protection against misuse and invalid input:

### Layer 1 — Code (`guardrails.py`)
| Check | Description |
|---|---|
| Length | Rejects requests under 10 or over 2000 characters |
| Insurance relevance | Requires at least one insurance-related keyword or intent phrase |
| Prompt injection | Detects phrases like "ignore previous instructions", "you are now", "act as" |
| Blocked topics | Rejects fraud, illegal activity, hacking, terrorism, money laundering |
| Sensitive data | Detects real SSNs, credit card numbers, emails, phone numbers |

### Layer 2 — Prompt (`prompts/system_prompt.md`)
- LLM refuses off-topic requests
- LLM refuses fraud or illegal content with a defined fallback response
- LLM ignores prompt injection attempts with active instruction and fallback output
- No hallucinated legal advice
- No filler or explanatory output — only policy document text

---

## Engineering Improvement

**Reflection / Self-Check**

After all 9 sections are generated, the agent makes one final LLM call to review the completed policy against the original request. It checks:
- Are all 9 required sections present?
- Are there any gaps based on the user's specific request?
- What improvements would make the policy more complete?

The reflection result (passed/failed, issues, improvements) is available in the API response but not included in the final document — keeping the output clean.

This demonstrates autonomous self-evaluation and closes the agent loop.

---

## Project Structure

```
Flud Ai/
├── agent.py                 Core agent loop
├── document_generator.py    Word document builder
├── groq_client.py           Groq LLM wrapper
├── guardrails.py            Input validation
├── main.py                  FastAPI application
├── models.py                Pydantic models + exceptions
├── run.py                   CLI runner
├── requirements.txt         Pinned dependencies
├── sample_inputs.txt        Ready-to-use test cases
├── .env.example             Environment variable template
├── .gitignore               Git ignore rules
├── prompts/
│   └── system_prompt.md     LLM system prompt
└── generated_docs/          Output directory (gitignored)
```

---

## Setup

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for full step-by-step instructions.

**Quick start:**

```bash
# 1. Clone the repo
git clone <repo-url>
cd "Flud Ai"

# 2. Run the setup script
python setup.py

# 3. Add your Groq API key to .env
# Get a free key at https://console.groq.com

# 4. Run
python run.py
```

---

## Usage

### Option 1 — CLI (recommended)

```bash
python run.py
```

Enter your request at the prompt. The agent runs with a live spinner and saves the `.docx` on completion.

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

Swagger UI: `http://localhost:8000/docs`

Health check: `http://localhost:8000/health`

---

## Sample Inputs

**Standard:**
```
Generate a health insurance policy for a 30-year-old male, non-smoker, no pre-existing conditions, working as a software engineer, looking for individual coverage with dental and vision add-ons.
```

**Complex / Ambiguous:**
```
I need an insurance policy for a 45-year-old female who smokes occasionally, has been diagnosed with type 2 diabetes for 3 years and takes metformin daily, and runs a small home-based bakery business with two part-time employees and commercial-grade kitchen equipment worth around $15,000. She owns her home valued at approximately $320,000 with a mortgage, has a 16-year-old dependent child, and her husband passed away two years ago. She wants health coverage for herself including dental and vision, property coverage for both her home and the business equipment inside it, and is unsure whether to add life insurance given her dependent child but is worried about the higher premium. She has not decided on a deductible amount, does not know whether to go with a PPO or HMO, and is open to suggestions on riders. Her annual income from the bakery is roughly $48,000 and she has no other insurance currently.
```

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
    { "task_id": 1, "task_name": "Declarations Page", "status": "completed" }
  ],
  "reflection": {
    "passed": true,
    "issues_found": [],
    "improvements_made": []
  },
  "document_path": "insurance_policy_20240101_120000_abc12345.docx",
  "download_url": "/download?filename=insurance_policy_...",
  "message": "Insurance policy generated successfully."
}
```

**Error codes:**
| Code | Meaning |
|---|---|
| 400 | Empty request |
| 422 | Guardrail blocked |
| 502 | LLM API failure |
| 504 | Agent timed out |

### `GET /download?filename=<filename>`

Downloads a generated `.docx` file.

### `GET /health`

Returns API and LLM connectivity status.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins |

---

## Design Decisions & Tradeoffs

### Fixed Task Plan vs LLM-Generated Tasks
The 9 policy section names are hardcoded rather than generated by the LLM. Early versions asked the LLM to generate task names, which produced verbose descriptions that leaked into the document output. Fixed names give consistent, clean section headings every time.

### Autonomous Planning vs Deterministic Workflow
The agent uses a deterministic 9-task structure (ensuring all required sections are always present) while keeping the content of each section fully autonomous (the LLM decides what to write based on the applicant's profile). This balances reliability with genuine autonomous reasoning.

### Reflection as Self-Check
Rather than using multi-agent architecture (separate validator agent), a single reflection call at the end reviews the agent's own output. This keeps the system simple, reduces token usage, and is sufficient for the scope of this use case.

### Groq Free Tier
Using Groq's free tier means a 100,000 token/day limit. Each full policy run uses approximately 10,000–15,000 tokens across all LLM calls. The retry logic with exponential backoff handles per-minute rate limits automatically.
