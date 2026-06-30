import re
import logging

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

MIN_LENGTH = 10
MAX_LENGTH = 2000

# Expanded to cover intent-based phrases, not just insurance jargon
INSURANCE_KEYWORDS = [
    "insurance", "policy", "coverage", "premium", "claim", "deductible",
    "beneficiary", "insured", "insurer", "health", "life", "property",
    "dental", "vision", "liability", "underwrite", "rider", "exclusion",
    "copay", "coinsurance", "annuity", "indemnity", "risk", "accident",
    "disability", "term", "whole life", "medical", "auto", "home", "business",
    # Intent-based phrases
    "protect", "protection", "coverage for", "financial protection",
    "death benefit", "monthly payment", "plan for", "cover my",
    "protect my family", "financial hardship", "secure my",
]

SENSITIVE_PATTERNS = {
    "SSN": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    # Tightened: require explicit phone formatting (parens, dashes, or +1 prefix)
    "Phone Number": r'(\+1[-\s]?\(?\d{3}\)?[-\s]\d{3}[-\s]\d{4}|\(\d{3}\)\s?\d{3}[-\s]\d{4})',
    "Credit Card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "Email Address": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
}

# Blocked content topics
BLOCKED_TOPICS = [
    "hack", "exploit", "bypass", "jailbreak", "illegal", "fraud",
    "scam", "fake claim", "money laundering", "terrorism",
]

# Prompt injection patterns — kept separate for clarity
PROMPT_INJECTION_PATTERNS = [
    r'ignore (previous|prior|all) instructions',
    r'you are now',
    r'disregard your (rules|instructions|guidelines)',
    r'forget your (previous|prior) instructions',
    r'act as (a|an)',
    r'pretend (you are|to be)',
    r'your new (role|instructions|task) (is|are)',
    r'do not follow',
    r'override (your|the) (system|instructions)',
    r'new system prompt',
]


# ── Guardrail checks ───────────────────────────────────────────────────────────

def check_length(request: str) -> tuple[bool, str]:
    length = len(request.strip())
    if length < MIN_LENGTH:
        return False, "Request is too short. Please provide more details about the insurance policy you need."
    if length > MAX_LENGTH:
        return False, f"Request is too long. Please keep your request under {MAX_LENGTH} characters."
    return True, ""


def check_insurance_relevance(request: str) -> tuple[bool, str]:
    lower = request.lower()
    if not any(keyword in lower for keyword in INSURANCE_KEYWORDS):
        return False, (
            "This request does not appear to be related to insurance. "
            "Please describe the type of insurance policy you need."
        )
    return True, ""


def check_blocked_topics(request: str) -> tuple[bool, str]:
    lower = request.lower()
    for topic in BLOCKED_TOPICS:
        if topic in lower:
            return False, (
                f"This request contains content that cannot be processed: '{topic}'. "
                "Please submit a valid insurance policy request."
            )
    return True, ""


def check_prompt_injection(request: str) -> tuple[bool, str]:
    lower = request.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return False, "This request contains invalid instructions and cannot be processed."
    return True, ""


def check_sensitive_data(request: str) -> tuple[bool, str]:
    for label, pattern in SENSITIVE_PATTERNS.items():
        if re.search(pattern, request):
            return False, (
                f"Your request appears to contain a real {label}. "
                "Please do not include personal sensitive information. "
                "Use placeholder values like 'John Doe', 'Age 35', etc."
            )
    return True, ""


# ── Main validator ─────────────────────────────────────────────────────────────

class GuardrailError(Exception):
    pass


def validate_request(request: str):
    """
    Run all guardrail checks on the incoming request.
    Security checks (injection, sensitive data, blocked topics) fail fast.
    Raises GuardrailError with a user-friendly message if any check fails.

    NOTE: BLOCKED_TOPICS and PROMPT_INJECTION_PATTERNS here must be kept
    in sync with the guardrail rules defined in prompts/system_prompt.md.
    """
    # Security-critical checks — fail fast
    security_checks = [
        check_prompt_injection,
        check_blocked_topics,
        check_sensitive_data,
    ]
    for check in security_checks:
        passed, message = check(request)
        if not passed:
            logger.warning("Guardrail blocked request [%s]: %s", check.__name__, message)
            raise GuardrailError(message)

    # Content/format checks
    content_checks = [
        check_length,
        check_insurance_relevance,
    ]
    for check in content_checks:
        passed, message = check(request)
        if not passed:
            logger.info("Guardrail rejected request [%s]: %s", check.__name__, message)
            raise GuardrailError(message)
