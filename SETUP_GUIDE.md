# Setup Guide — Insurance Policy Generation Agent

This guide walks you through replicating the project in a fresh environment from scratch.

---

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Minimum Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |

You will also need a **free Groq API key**:
1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to **API Keys** and create a new key
4. Copy the key — you will need it in Step 4

---

## Step 1 — Get the Code

**Option A — Clone from GitHub:**
```bash
git clone <your-repo-url>
cd "Flud Ai"
```

**Option B — Download as ZIP:**
1. Download and extract the ZIP from GitHub
2. Open a terminal and navigate into the extracted folder

---

## Step 2 — Create a Virtual Environment

It is strongly recommended to use a virtual environment to isolate dependencies.

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt after activation.

---

## Step 3 — Install Dependencies

**Option A — Automated (recommended):**
```bash
python setup.py
```

**Option B — Manual:**
```bash
pip install -r requirements.txt
```

This installs the following packages:
| Package | Purpose |
|---|---|
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server for FastAPI |
| `groq` | Official Groq Python SDK |
| `python-docx` | Word document generation |
| `pydantic` | Request/response validation |
| `python-dotenv` | Environment variable loading |
| `httpx` | HTTP client for Groq SSL fix |

---

## Step 4 — Configure Environment Variables

Copy the example environment file:

**Windows:**
```bash
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your values:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

- `GROQ_API_KEY` — **Required.** Your key from [console.groq.com](https://console.groq.com)
- `GROQ_MODEL` — Optional. Defaults to `llama-3.3-70b-versatile`
- `CORS_ORIGINS` — Optional. Only relevant if calling the API from a frontend

---

## Step 5 — Verify Setup

Run a quick check to confirm everything is working:

```bash
python -c "from groq_client import call_llm; print(call_llm('say OK'))"
```

Expected output:
```
OK
```

If you see an error about the API key, double-check your `.env` file.

---

## Step 6 — Run the Project

### CLI Mode (recommended for demo)

```bash
python run.py
```

Enter your insurance request at the prompt. The agent will run with a live spinner and save the `.docx` file in the project folder.

### API Mode

Start the server:

```bash
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.

Open Swagger UI at: `http://localhost:8000/docs`

Test with curl:
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d "{\"request\": \"Generate a health insurance policy for a 30-year-old male software engineer.\"}"
```

---

## Troubleshooting

### SSL Certificate Error (Windows)
If you see `SSL: CERTIFICATE_VERIFY_FAILED`, this is a known Windows Python issue. It is already handled in `groq_client.py` via `httpx.Client(verify=False)`. No action needed.

### Rate Limit Error (429)
Groq's free tier allows 100,000 tokens per day. If you hit the limit:
- The agent will automatically retry up to 3 times with backoff for per-minute limits
- For daily limits, wait for the limit to reset (usually within the hour)
- The error message will tell you exactly how long to wait

### Module Not Found
Make sure your virtual environment is activated:
```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Then reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Empty .env File
If the application crashes on startup with an `EnvironmentError`, your `.env` file is missing or the API key is not set. See Step 4.

---

## Project Structure Reference

```
Flud Ai/
├── agent.py                 Core agent loop (4 steps)
├── document_generator.py    Word document builder
├── groq_client.py           Groq LLM wrapper
├── guardrails.py            Input validation and guardrails
├── main.py                  FastAPI application
├── models.py                Pydantic models and custom exceptions
├── run.py                   CLI runner with spinner
├── setup.py                 Automated setup script
├── requirements.txt         Pinned Python dependencies
├── sample_inputs.txt        Test case inputs
├── .env                     Your environment variables (never commit this)
├── .env.example             Safe template for .env
├── .gitignore               Git ignore rules
├── prompts/
│   └── system_prompt.md     LLM system prompt
└── generated_docs/          Generated .docx files (gitignored)
```

---

## Notes

- The `generated_docs/` folder is gitignored — generated policy documents are not uploaded to GitHub
- The `.env` file is gitignored — your API key is never committed
- All generated documents are for demonstration purposes only
- Consult a licensed insurance professional for real coverage decisions
