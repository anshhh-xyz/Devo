"""Check presets defining immutable verification commands."""
from dataclasses import dataclass, field
import sys
from pathlib import Path


@dataclass(frozen=True)
class CheckPreset:
    name: str
    timeout_sec: float = 30.0
    output_cap_bytes: int = 100 * 1024  # 100 KB

    def build_argv(self, junit_path: Path | str) -> list[str]:
        """Build the immutable argument list for the check command."""
        return [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--junitxml={Path(junit_path).resolve()}",
            "-p",
            "no:cacheprovider",
        ]


BUILTIN_PRESETS: dict[str, CheckPreset] = {
    "pytest": CheckPreset(name="pytest", timeout_sec=30.0),
}


def get_preset(name: str = "pytest") -> CheckPreset:
    """Retrieve a built-in check preset by name."""
    if name not in BUILTIN_PRESETS:
        raise ValueError(f"Unknown preset: '{name}'. Available presets: {list(BUILTIN_PRESETS.keys())}")
    return BUILTIN_PRESETS[name]
