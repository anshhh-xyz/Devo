"""Generic hosted API model adapter using standard JSON endpoints."""
import json
import os
import urllib.request
from devo.model.adapter import ModelAdapter
from devo.model.prompts import SYSTEM_PROMPT, build_user_prompt
from devo.model.schema import ModelProposal, validate_model_proposal
from devo.verdict.compute_verdict import CheckResult


class ApiModelAdapter(ModelAdapter):
    """Invokes an LLM chat completion API and validates structured output."""

    def __init__(
        self,
        api_key_env: str = "DEVO_API_KEY",
        endpoint: str = "https://api.openai.com/v1/chat/completions",
        model_name: str = "gpt-4o-mini",
    ) -> None:
        self.api_key_env = api_key_env
        self.endpoint = endpoint
        self.model_name = model_name

    def propose_edits(
        self,
        task: str,
        files: dict[str, str],
        baseline: CheckResult,
        constraints: dict | None = None,
    ) -> ModelProposal:
        api_key = os.environ.get(self.api_key_env) or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(f"API key missing. Please set {self.api_key_env} or OPENAI_API_KEY environment variable.")

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
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        text = data["choices"][0]["message"]["content"]
        proposal_dict = json.loads(text)
        proposal = validate_model_proposal(proposal_dict)
        proposal.raw_response = text
        return proposal
