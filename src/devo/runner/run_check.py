"""Subprocess runner for check execution with sandboxed limits."""
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from devo.runner.parse_junit import parse_junit_xml
from devo.runner.presets import CheckPreset, get_preset
from devo.verdict.compute_verdict import CheckResult


SENSITIVE_KEY_PREFIXES = (
    "OPENAI_",
    "ANTHROPIC_",
    "GEMINI_",
    "GOOGLE_",
    "DEVO_",
    "AWS_",
    "GITHUB_",
    "API_KEY",
    "SECRET",
    "TOKEN",
)


SENSITIVE_SUBSTRINGS = (
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "AUTH",
    "CREDENTIAL",
)


def scrub_environment(env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a scrubbed copy of environment variables, stripping API keys and secrets."""
    base = os.environ if env is None else env
    scrubbed = {}
    for k, v in base.items():
        k_upper = k.upper()
        if (
            any(k_upper.startswith(prefix) for prefix in SENSITIVE_KEY_PREFIXES)
            or any(sub in k_upper for sub in SENSITIVE_SUBSTRINGS)
        ):
            continue
        scrubbed[k] = v
    return scrubbed


def kill_process_tree(pid: int) -> None:
    """Kill a process and all of its descendants across platforms."""
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, check=False)
        except Exception:
            pass
    else:
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass


def run_check(
    workspace: Path | str,
    preset: CheckPreset | None = None,
    timeout_override: float | None = None,
    extra_env: dict[str, str] | None = None,
) -> CheckResult:
    """Execute a verification check on the given workspace.

    Enforces:
    - shell=False
    - fixed cwd (the workspace)
    - timeout with process-tree termination
    - output cap
    - scrubbed environment
    - external temp directory for JUnit XML
    """
    workspace_path = Path(workspace).resolve()
    if not workspace_path.is_dir():
        return CheckResult(
            status="spawn_error",
            exit_code=-1,
            reason=f"Workspace directory not found: {workspace_path}",
        )

    preset = preset or get_preset("pytest")
    timeout_sec = timeout_override if timeout_override is not None else preset.timeout_sec
    env = scrub_environment(extra_env)

    with tempfile.TemporaryDirectory() as temp_dir:
        junit_file = Path(temp_dir) / "junit.xml"
        argv = preset.build_argv(junit_file)

        creationflags = 0
        preexec_fn = None
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            preexec_fn = os.setsid

        start_time = time.monotonic()
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                shell=False,
                creationflags=creationflags,
                preexec_fn=preexec_fn,
                text=True,
                errors="replace",
            )
        except (FileNotFoundError, OSError) as err:
            return CheckResult(
                status="spawn_error",
                exit_code=-1,
                reason=f"Failed to spawn process {argv[0]}: {err}",
            )

        truncated = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            kill_process_tree(proc.pid)
            stdout, stderr = proc.communicate()
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return CheckResult(
                status="timeout",
                exit_code=-1,
                duration_ms=duration_ms,
                stdout=stdout[: preset.output_cap_bytes],
                stderr=stderr[: preset.output_cap_bytes],
                reason=f"Process exceeded timeout limit of {timeout_sec}s",
            )

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Output capping
        if len(stdout) > preset.output_cap_bytes:
            stdout = stdout[: preset.output_cap_bytes] + "\n...[OUTPUT TRUNCATED]"
            truncated = True
        if len(stderr) > preset.output_cap_bytes:
            stderr = stderr[: preset.output_cap_bytes] + "\n...[OUTPUT TRUNCATED]"
            truncated = True

        junit_counts = parse_junit_xml(junit_file)

        return CheckResult(
            status="completed",
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            stdout=stdout,
            stderr=stderr,
            truncated=truncated,
            junit_ok=junit_counts.ok,
            tests=junit_counts.tests,
            failures=junit_counts.failures,
            errors=junit_counts.errors,
            skipped=junit_counts.skipped,
            reason=junit_counts.reason,
        )
