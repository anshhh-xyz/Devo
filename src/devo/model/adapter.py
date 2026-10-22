"""Model adapter interface defining proposal generation."""
from abc import ABC, abstractmethod
from devo.model.schema import ModelProposal
from devo.verdict.compute_verdict import CheckResult


class ModelAdapter(ABC):
    """Abstract base class for model proposal backends."""

    @abstractmethod
    def propose_edits(
        self,
        task: str,
        files: dict[str, str],
        baseline: CheckResult,
        constraints: dict | None = None,
    ) -> ModelProposal:
        """Generate a structured plan and edits given task context and baseline check results."""
        pass
