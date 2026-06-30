# Setup Guide — Insurance Policy Generation Agent

This guide walks you through setting up and running the project in a fresh environment from scratch.

---

## Prerequisites

| Tool | Minimum Version | How to check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |

You will also need a **free Groq API key**:
1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key — you will need it in Step 4

---

## Step 1 — Get the Code

```bash
git clone https://github.com/Hemananth-13/Policy-Agent.git
cd Policy-Agent
```

Or download the ZIP from GitHub and extract it, then open a terminal inside the folder.

---

## Step 2 — Run the Setup Script

The automated setup script handles everything — virtual environment, dependencies, and `.env` file:

```bash
python setup.py
```

**What it does:**
1. Checks Python version (3.10+ required)
2. Creates a `.venv` virtual environment
3. Upgrades pip
4. Installs all pinned dependencies from `requirements.txt`
5. Copies `.env.example` → `.env` if `.env` doesn't exist yet
6. Prints the next steps

**Expected output:**
```
============================================================
  Insurance Policy Generation Agent — Setup
============================================================

  Checking Python version...
  [OK] Python 3.11 detected

  Creating virtual environment (.venv)...
  [OK] .venv created

  Upgrading pip...
  [OK] pip upgraded

  Installing dependencies from requirements.txt...
  [OK] All dependencies installed

  Setting up .env file...
  [OK] .env created from .env.example

============================================================
  Setup complete!
============================================================

  Next steps:

  1. Activate the virtual environment:
       .venv\Scripts\activate

  2. Add your Groq API key to .env:
       GROQ_API_KEY=your_actual_key_here
       Get a free key at: https://console.groq.com

  3. Run the agent:
       python run.py
```

---

## Step 3 — Activate the Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt after activation.

---

## Step 4 — Add Your Groq API Key

Open the `.env` file in any text editor and replace the placeholder:

```
GROQ_API_KEY=your_groq_api_key_here   ← replace this
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Variable reference:**

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | — | Your Groq API key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Comma-separated allowed CORS origins |

> **Important:** Never commit your `.env` file. It is already listed in `.gitignore`.

---

## Step 5 — Verify the Setup

Run a quick connectivity check to confirm the API key is working:

```bash
python -c "from groq_client import call_llm; print(call_llm('say OK', max_tokens=5))"
```

Expected output:
```
OK
```

If you see an `EnvironmentError` — your API key is not set in `.env`.  
If you see an SSL error — it is already handled automatically in `groq_client.py`.

---

## Step 6 — Run the Agent

### CLI Mode (recommended)

```bash
python run.py
```

Enter your insurance request at the prompt. You will see a live spinner:

```
------------------------------------------------------------

  Insurance Policy Generation Agent
  Powered by Groq LLM + Autonomous Planning

------------------------------------------------------------

Enter your insurance policy request:
> Generate a health insurance policy for a 30-year-old male...

------------------------------------------------------------

  ⠹  Analysing request       ...
  ⠸  Planning policy sections...
  ⠼  Writing policy content  ...
  ⠴  Running quality check   ...
  [OK]  Document ready

------------------------------------------------------------

Policy Sections Generated:
  [DONE]  Declarations Page
  [DONE]  Insuring Agreement
  [DONE]  Risk Assessment and Underwriting Summary
  [DONE]  Coverage Details
  [DONE]  Premium Schedule
  [DONE]  Policy Conditions
  [DONE]  Exclusions
  [DONE]  Riders and Endorsements
  [DONE]  Definitions

Quality Check:
  Status: PASSED

------------------------------------------------------------

Document saved to:
  C:\...\generated_docs\insurance_policy_20240101_120000_abc12345.docx
```

The `.docx` file is saved in the `generated_docs/` folder.

### API Mode

Start the server:

```bash
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`.

- **Swagger UI:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

Send a request with curl:

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d "{\"request\": \"Generate a health insurance policy for a 30-year-old male software engineer.\"}"
```

---

## Sample Inputs

Ready-to-use test cases are in `sample_inputs.txt`. Copy each as a single line.

**Test Case 1 — Standard:**
```
Generate a health insurance policy for a 30-year-old male, non-smoker, no pre-existing conditions, working as a software engineer, looking for individual coverage with dental and vision add-ons.
```

**Test Case 2 — Complex / Ambiguous:**
```
I need an insurance policy for a 45-year-old female who smokes occasionally, has been diagnosed with type 2 diabetes for 3 years and takes metformin daily, and runs a small home-based bakery business with two part-time employees and commercial-grade kitchen equipment worth around $15,000. She owns her home valued at approximately $320,000 with a mortgage, has a 16-year-old dependent child, and her husband passed away two years ago. She wants health coverage for herself including dental and vision, property coverage for both her home and the business equipment inside it, and is unsure whether to add life insurance given her dependent child but is worried about the higher premium. She has not decided on a deductible amount, does not know whether to go with a PPO or HMO, and is open to suggestions on riders. Her annual income from the bakery is roughly $48,000 and she has no other insurance currently.
```

---

## Installed Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.136.1 | REST API framework |
| `uvicorn` | 0.46.0 | ASGI server |
| `groq` | 1.5.0 | Official Groq Python SDK |
| `python-docx` | 1.2.0 | Word document generation |
| `pydantic` | 2.13.2 | Request/response validation |
| `python-dotenv` | 1.2.2 | Environment variable loading |
| `httpx` | 0.28.1 | HTTP client (SSL fix for Groq on Windows) |

---

## Troubleshooting

### SSL Certificate Error
```
SSL: CERTIFICATE_VERIFY_FAILED
```
This is a known Windows Python issue. It is already fixed in `groq_client.py` via `httpx.Client(verify=False)`. No action needed.

---

### API Key Not Set
```
EnvironmentError: GROQ_API_KEY is not set.
```
Open `.env` and ensure your key is set:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

---

### Rate Limit Hit (429)
```
[LLM ERROR] LLM call failed: Rate limit reached... try again in Xm Xs
```
Groq's free tier allows 100,000 tokens/day and 6,000 tokens/minute.
- The agent automatically retries up to **3 times** with backoff (2s → 5s → 10s) for per-minute limits
- For daily limits, wait the time shown in the error message and run again
- Each full policy run uses approximately 10,000–15,000 tokens

---

### Virtual Environment Not Activated
```
ModuleNotFoundError: No module named 'fastapi'
```
Activate the virtual environment first:
```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

---

### All Tasks Failed
```
[FAIL]  Declarations Page
[FAIL]  Insuring Agreement
...
```
This usually means a regex or code error in the agent. Check the terminal for `[ERROR]` output above the task list. The most common cause is a rate limit hit before tasks start — wait and retry.

---

## Project Structure

```
Policy-Agent/
├── agent.py                 Core agent loop (extract, plan, execute, reflect)
├── document_generator.py    Word document builder — 9 sections only
├── groq_client.py           Groq LLM wrapper with SSL fix and token logging
├── guardrails.py            Input validation — 5 checks across 2 categories
├── main.py                  FastAPI application
├── models.py                Pydantic models + AgentError, LLMError, DocumentError
├── run.py                   CLI runner with spinner animation
├── setup.py                 Automated setup script
├── requirements.txt         Pinned Python dependencies
├── sample_inputs.txt        Ready-to-use test cases
├── .env.example             Environment variable template (safe to commit)
├── .env                     Your actual keys (never commit this)
├── .gitignore               Excludes .env, generated_docs/, __pycache__/
├── prompts/
│   └── system_prompt.md     LLM system prompt loaded at runtime
└── generated_docs/          Generated .docx output files (gitignored)
```
