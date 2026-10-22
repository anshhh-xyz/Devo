"""Mock model adapter replaying recorded fixture scenarios."""
import json
from pathlib import Path
from devo.model.adapter import ModelAdapter
from devo.model.schema import ModelProposal, validate_model_proposal
from devo.verdict.compute_verdict import CheckResult


class MockModelAdapter(ModelAdapter):
    """Replays deterministic proposal fixtures for tests and reproducible demos."""

    def __init__(self, scenario: str = "scenario_verified", fixtures_dir: Path | str = "fixtures/model") -> None:
        self.scenario = scenario
        self.fixtures_dir = Path(fixtures_dir)

    def propose_edits(
        self,
        task: str,
        files: dict[str, str],
        baseline: CheckResult,
        constraints: dict | None = None,
    ) -> ModelProposal:
        # Check if scenario is a file path or name
        candidate = Path(self.scenario)
        if not candidate.exists():
            candidate = self.fixtures_dir / f"{self.scenario}.json"

        if not candidate.exists():
            raise FileNotFoundError(f"Mock scenario fixture not found: {self.scenario} (looked at {candidate})")

        with open(candidate, "r", encoding="utf-8") as f:
            data = json.load(f)

        proposal = validate_model_proposal(data)
        proposal.raw_response = json.dumps(data)
        return proposal
