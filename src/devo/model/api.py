"""Generic hosted API model adapter supporting Groq, Gemini, and OpenAI-compatible endpoints."""
import json
import os
import re
import urllib.request
from devo.model.adapter import ModelAdapter
from devo.model.prompts import SYSTEM_PROMPT, build_user_prompt
from devo.model.schema import ModelProposal, validate_model_proposal
from devo.verdict.compute_verdict import CheckResult


def detect_api_credentials(
    explicit_key: str | None = None,
    explicit_endpoint: str | None = None,
    explicit_model: str | None = None,
) -> tuple[str, str, str]:
    """Detect available API key, endpoint, and default model name across providers."""
    # 1. Groq keys (GROQ_API_KEY, GROQ_API_KEY_1, ..., GROQ_API_KEY_4)
    groq_candidates = ["GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4"]
    for k in groq_candidates:
        val = os.environ.get(k)
        if val:
            endpoint = explicit_endpoint or "https://api.groq.com/openai/v1/chat/completions"
            model = explicit_model or "qwen/qwen3.8-27b"
            return val, endpoint, model

    # 2. Gemini key (GEMINI_API_KEY)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        endpoint = explicit_endpoint or "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        model = explicit_model or "gemini-2.0-flash"
        return gemini_key, endpoint, model

    # 3. OpenAI / generic DEVO_API_KEY
    for k in ["DEVO_API_KEY", "OPENAI_API_KEY"]:
        val = os.environ.get(k)
        if val:
            endpoint = explicit_endpoint or "https://api.openai.com/v1/chat/completions"
            model = explicit_model or "gpt-4o-mini"
            return val, endpoint, model

    # 4. Explicit key if passed
    if explicit_key:
        endpoint = explicit_endpoint or "https://api.groq.com/openai/v1/chat/completions"
        model = explicit_model or "qwen/qwen3.8-27b"
        return explicit_key, endpoint, model

    raise ValueError(
        "No API key found in environment.\n"
        "Please set one of:\n"
        "  - GROQ_API_KEY (or GROQ_API_KEY_1..4)\n"
        "  - GEMINI_API_KEY\n"
        "  - OPENAI_API_KEY or DEVO_API_KEY"
    )


class ApiModelAdapter(ModelAdapter):
    """Invokes an LLM chat completion API and validates structured output."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.api_key, self.endpoint, self.model_name = detect_api_credentials(
            explicit_key=api_key,
            explicit_endpoint=endpoint,
            explicit_model=model_name,
        )

    def propose_edits(
        self,
        task: str,
        files: dict[str, str],
        baseline: CheckResult,
        constraints: dict | None = None,
    ) -> ModelProposal:
        user_content = build_user_prompt(task, files, baseline)
        payload = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Devo/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        text = data["choices"][0]["message"]["content"]

        # Clean potential markdown wrappers e.g. ```json ... ```
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned).strip()

        proposal_dict = json.loads(cleaned)
        proposal = validate_model_proposal(proposal_dict)
        proposal.raw_response = text
        return proposal
