import os
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from models import AgentRequest, AgentResponse, TaskItem, ReflectionNote, LLMError, DocumentError, AgentError
from agent import run_agent
from document_generator import generate_document, OUTPUT_DIR
from guardrails import validate_request, GuardrailError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_TIMEOUT_SECONDS = 300

app = FastAPI(
    title="Insurance Policy Generation Agent",
    description="Autonomous AI agent that generates professional insurance policy documents.",
    version="1.0.0",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "running", "agent": "Insurance Policy Generation Agent"}


@app.get("/health")
async def deep_health_check():
    """Verify Groq LLM connectivity in addition to app status."""
    try:
        from groq_client import call_llm
        call_llm("Reply with the single word: OK", max_tokens=5)
        return {"status": "healthy", "llm": "connected", "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "llm": "unreachable", "detail": str(e)})


@app.post("/agent", response_model=AgentResponse)
async def generate_policy(body: AgentRequest):
    if not body.request.strip():
        raise HTTPException(status_code=400, detail="Request cannot be empty.")

    try:
        validate_request(body.request)
    except GuardrailError as e:
        raise HTTPException(status_code=422, detail=f"[GUARDRAIL] {str(e)}")

    try:
        # Run blocking agent in a thread so the event loop is not blocked
        result = await asyncio.wait_for(
            asyncio.to_thread(run_agent, body.request),
            timeout=AGENT_TIMEOUT_SECONDS,
        )

        doc_path = await asyncio.to_thread(
            generate_document,
            request=body.request,
            policy_details=result["policy_details"],
            tasks=result["tasks"],
            reflection=result["reflection"],
        )

        tasks_out = [
            TaskItem(task_id=t.task_id, task_name=t.task_name, status=t.status)
            for t in result["tasks"]
        ]
        reflection: ReflectionNote = result["reflection"]
        filename = Path(doc_path).name

        return AgentResponse(
            request=body.request,
            tasks=tasks_out,
            reflection=reflection,
            document_path=filename,
            message="Insurance policy generated successfully.",
            download_url=f"/download?filename={filename}",
        )

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out. Please try again.")
    except LLMError as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail=f"LLM error: {str(e)}")
    except DocumentError as e:
        logger.exception("Document generation failed")
        raise HTTPException(status_code=500, detail=f"Document error: {str(e)}")
    except AgentError as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/download")
async def download_document(filename: str):
    # Resolve path and validate it stays within OUTPUT_DIR — prevents path traversal
    safe_path = (OUTPUT_DIR / filename).resolve()
    if not safe_path.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")

    return FileResponse(
        path=str(safe_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
