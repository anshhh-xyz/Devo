"""Schema validation for structured model proposals."""
from dataclasses import dataclass, field
from typing import Any


class ModelProposalSchemaError(ValueError):
    """Raised when model proposal does not adhere to the required schema."""
    pass


@dataclass
class ProposedPlan:
    summary: str
    files: list[str] = field(default_factory=list)
    approach: str = ""


@dataclass
class ProposedEdit:
    path: str
    old_str: str
    new_str: str


@dataclass
class ModelProposal:
    plan: ProposedPlan
    edits: list[ProposedEdit]
    raw_response: str = ""


def validate_model_proposal(data: Any) -> ModelProposal:
    """Validate and parse structured proposal dictionary from model into ModelProposal.

    Rejects malformed data strictly without endless retries.
    """
    if not isinstance(data, dict):
        raise ModelProposalSchemaError("Proposal must be a JSON object")

    plan_raw = data.get("plan")
    if not isinstance(plan_raw, dict):
        raise ModelProposalSchemaError("Proposal must include a 'plan' object")

    summary = plan_raw.get("summary")
    if not summary or not isinstance(summary, str):
        raise ModelProposalSchemaError("Plan must include a non-empty string 'summary'")

    files = plan_raw.get("files", [])
    if not isinstance(files, list):
        raise ModelProposalSchemaError("Plan 'files' must be a list of file paths")

    approach = plan_raw.get("approach", "")

    edits_raw = data.get("edits")
    if not isinstance(edits_raw, list) or not edits_raw:
        raise ModelProposalSchemaError("Proposal must include a non-empty 'edits' list")

    parsed_edits: list[ProposedEdit] = []
    for idx, e in enumerate(edits_raw):
        if not isinstance(e, dict):
            raise ModelProposalSchemaError(f"Edit #{idx + 1} must be an object")

        path = e.get("path")
        old_str = e.get("old_str")
        new_str = e.get("new_str")

        if not path or not isinstance(path, str):
            raise ModelProposalSchemaError(f"Edit #{idx + 1} missing string 'path'")
        if old_str is None or not isinstance(old_str, str):
            raise ModelProposalSchemaError(f"Edit #{idx + 1} missing string 'old_str'")
        if new_str is None or not isinstance(new_str, str):
            raise ModelProposalSchemaError(f"Edit #{idx + 1} missing string 'new_str'")

        parsed_edits.append(ProposedEdit(path=path, old_str=old_str, new_str=new_str))

    return ModelProposal(
        plan=ProposedPlan(summary=summary, files=files, approach=str(approach)),
        edits=parsed_edits,
    )
