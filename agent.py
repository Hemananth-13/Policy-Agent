import json
import re
import time
import logging
from groq_client import call_llm
from models import TaskItem, ReflectionNote, LLMError, AgentError

logger = logging.getLogger(__name__)

REQUIRED_TASK_COUNT = 9
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]


# ──────────────────────────────────────────────
# Utility: retry wrapper for LLM calls
# ──────────────────────────────────────────────
def call_llm_with_retry(prompt: str, temperature: float = 0.5, max_tokens: int = 2048) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            return call_llm(prompt, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "503" in error_str
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF[attempt]
                logger.warning("Rate limit hit. Retrying in %ds (attempt %d/%d)...", wait, attempt + 1, MAX_RETRIES)
                time.sleep(wait)
            else:
                raise LLMError(f"LLM call failed on attempt {attempt + 1}: {e}") from e
    raise LLMError("All LLM retry attempts exhausted.")


# ──────────────────────────────────────────────
# Utility: strip unwanted LLM filler content
# ──────────────────────────────────────────────
UNWANTED_PATTERNS = [
    r"^(introduction\s*[:\-]?\s*$)",
    r"^(conclusion\s*[:\-]?\s*$)",
    r"^(next steps?\s*[:\-]?\s*$)",
    r"^(final\s+\w+\s*(document|notes?|policy|clauses?)?\s*[:\-]?\s*$)",
    r"^(in this (task|section)[,.])",
    r"^(this (section|task) (covers|outlines|presents|provides|includes)[,.]?)",
    r"^(the (next|following) steps?[,.])",
    r"^(in conclusion[,.])",
    r"^(summary\s*[:\-]?\s*$)",
    r"^(overview\s*[:\-]?\s*$)",
    r"^(the (following|below) (section|details|information|content)[,.]?)",
    r"^(please note[,:])",
    r"^(note[,:]\s*this is a (mock|sample|demonstration))",
    r"^(the premium calculation for the)",
    r"^(based on the (information|details|data|risk profile) (provided|above|outlined))",
    r"^(the following (riders|exclusions|conditions|terms|definitions) (are|apply|outline))",
    r"^(these (exclusions|conditions|terms|factors) (apply|are applicable))",
    r"^(the (applicant|insured).{0,30}(risk|profile) (is|are|has been))",
]


def clean_llm_output(text: str, section_name: str = "") -> str:
    lines = text.splitlines()
    cleaned = []
    first_non_empty_done = False

    for line in lines:
        stripped = line.strip()

        # Skip section name on first non-empty line only
        if not first_non_empty_done and stripped:
            first_non_empty_done = True
            if section_name and stripped.lower() == section_name.lower():
                continue

        # Skip lines matching unwanted filler patterns
        skip = any(re.match(p, stripped, re.IGNORECASE) for p in UNWANTED_PATTERNS)
        if not skip:
            cleaned.append(line)

    # Strip trailing filler closing sentences from the last few lines
    CLOSING_PATTERNS = [
        r"^these (exclusions|conditions|terms|factors|riders|definitions) apply",
        r"^the policyholder can choose",
        r"^the insured is encouraged",
        r"^this concludes",
        r"^by signing",
        r"^for more information",
        r"^if you have any questions",
        r"^please (contact|consult|review|note)",
        r"^this policy is subject to",
        r"^this is a (mock|sample|demonstration)",
        r"^all (data|information|content) (is|are) for demonstration",
    ]
    while cleaned:
        last = cleaned[-1].strip()
        if not last or any(re.match(p, last, re.IGNORECASE) for p in CLOSING_PATTERNS):
            cleaned.pop()
        else:
            break

    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()


# ──────────────────────────────────────────────
# Utility: robust JSON extraction
# ──────────────────────────────────────────────
def extract_json_array(text: str) -> list:
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response.")
    return json.loads(match.group())


def extract_json_object(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*", "", text).strip("`").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(match.group())


# ──────────────────────────────────────────────
# Step 1: Extract structured policy details
# ──────────────────────────────────────────────
def extract_policy_details(request: str) -> str:
    prompt = f"""
Extract the key details from this insurance request and return them as structured labeled fields only. No prose, no explanations.

Request: "{request}"

Output format:
APPLICANT NAME: (generate a realistic full name)
AGE: 
GENDER: 
OCCUPATION: 
SMOKING STATUS: 
PRE-EXISTING CONDITIONS: 
LIFESTYLE: 
INSURANCE TYPE: 
COVERAGE TYPE: 
ADD-ONS REQUESTED: 
ASSUMED LOCATION: 
ASSUMED INCOME: 
ASSUMED DEDUCTIBLE: 
ASSUMED POLICY TERM: 
ASSUMPTIONS: (list only, one per line)

Return only the filled fields. No sentences. No paragraphs.
"""
    return call_llm_with_retry(prompt, temperature=0.3)


# ──────────────────────────────────────────────
# Step 2: Generate a task plan
# ──────────────────────────────────────────────
def plan_tasks(policy_details: str) -> list[TaskItem]:
    # Task names are fixed to the 9 required policy sections.
    # We do not ask the LLM to name them — it produces verbose descriptions.
    fixed_tasks = [
        "Declarations Page",
        "Insuring Agreement",
        "Risk Assessment and Underwriting Summary",
        "Coverage Details",
        "Premium Schedule",
        "Policy Conditions",
        "Exclusions",
        "Riders and Endorsements",
        "Definitions",
    ]
    return [TaskItem(task_id=i + 1, task_name=name) for i, name in enumerate(fixed_tasks)]


# ──────────────────────────────────────────────
# Step 3: Execute each task
# ──────────────────────────────────────────────
def execute_tasks(tasks: list[TaskItem], policy_details: str, log=None) -> list[TaskItem]:
    log = log or logger.info
    completed_summary = []

    for task in tasks:
        log(f"   >> Executing Task {task.task_id}/{len(tasks)}: {task.task_name}...")
        prior = ", ".join(completed_summary) if completed_summary else "None yet."

        prompt = f"""
You are a legal document writer producing a formal insurance policy contract.

Insurer: SecureHealth Insurance Co.
Applicant:
{policy_details}

Write ONLY the "{task.task_name}" section as it would appear word-for-word in a printed insurance policy booklet.

Do not write ANY of the following:
- Introductory sentences like "This section...", "The following...", "Below you will find..."
- Explanations of what you are doing
- Commentary or descriptions of the content
- Closing sentences like "These terms apply...", "The policyholder can choose...", "This concludes..."
- Anything that is not direct policy document text

Start immediately with the first field or clause. Use labeled fields, numbered clauses, and formal legal language throughout.
"""
        try:
            result = call_llm_with_retry(prompt, temperature=0.3, max_tokens=3000)
            result = clean_llm_output(result, task.task_name)
            task.result = result
            task.status = "completed"
            completed_summary.append(task.task_name)
            log(f"   >> Task {task.task_id} completed.")
        except Exception as e:
            task.result = f"Error: {str(e)}"
            task.status = "failed"
            log(f"   XX Task {task.task_id} failed: {str(e)}")

    return tasks


# ──────────────────────────────────────────────
# Step 4: Reflect and self-check
# ──────────────────────────────────────────────
def reflect(tasks: list[TaskItem], original_request: str) -> ReflectionNote:
    completed_tasks = ", ".join(t.task_name for t in tasks if t.status == "completed")
    failed_tasks = ", ".join(t.task_name for t in tasks if t.status == "failed")

    prompt = f"""
Review the following insurance policy generation job:

Original request: "{original_request}"
Completed sections: {completed_tasks}
Failed sections: {failed_tasks if failed_tasks else "None"}

Briefly assess:
1. Are all 9 required policy sections covered?
2. Any obvious gaps based on the request?
3. What improvements would make this policy more complete?

Return ONLY this JSON, no explanation:
{{
  "passed": true or false,
  "issues_found": ["issue 1", "issue 2"],
  "improvements_made": ["improvement 1", "improvement 2"]
}}
"""
    try:
        response = call_llm_with_retry(prompt, temperature=0.3)
        data = extract_json_object(response)
        return ReflectionNote(
            passed=data.get("passed", False),
            issues_found=data.get("issues_found", []),
            improvements_made=data.get("improvements_made", []),
        )
    except Exception as e:
        logger.warning("Reflection failed: %s. Using fallback.", str(e))
        all_done = all(t.status == "completed" for t in tasks)
        return ReflectionNote(
            passed=all_done,
            issues_found=[] if all_done else [
                f"Section '{t.task_name}' failed to generate." for t in tasks if t.status == "failed"
            ],
            improvements_made=["Reflection skipped due to API limit. All sections generated successfully."] if all_done else [],
        )


# ──────────────────────────────────────────────
# Main agent runner
# ──────────────────────────────────────────────
def run_agent(request: str, log=None) -> dict:
    log = log or logger.info
    log("[Agent] Request received.")

    log("\n[Step 1/4] Extracting policy details...")
    policy_details = extract_policy_details(request)
    log("  >> Policy details extracted.")

    log("\n[Step 2/4] Planning tasks...")
    tasks = plan_tasks(policy_details)
    log(f"  >> {len(tasks)} tasks planned:")
    for t in tasks:
        log(f"     - Task {t.task_id}: {t.task_name}")

    log("\n[Step 3/4] Executing tasks...")
    tasks = execute_tasks(tasks, policy_details, log=log)

    log("\n[Step 4/4] Reflecting on output...")
    reflection = reflect(tasks, request)
    status = "PASSED" if reflection.passed else "ISSUES FOUND - improvements applied"
    log(f"  >> Reflection: {status}")

    return {
        "policy_details": policy_details,
        "tasks": tasks,
        "reflection": reflection,
    }
