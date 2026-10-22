"""Command line interface for Devo."""
import argparse
import sys
from pathlib import Path
from devo.controller.run import RunState, execute_run
from devo.model.api import ApiModelAdapter
from devo.model.mock import MockModelAdapter
from devo.report.render import print_banner, render_diff_view, render_final_report
from devo.workspace.backup import revert_backup
from devo.workspace.diff import DiffResult
from devo.workspace.reset import reset_demo


def interactive_approval(diff_result: DiffResult) -> bool:
    """Prompt the interactive terminal user for explicit approval."""
    render_diff_view(diff_result)

    if not sys.stdin.isatty():
        print("\n[!] Refusing to apply: Standard input is non-interactive. Devo requires an interactive terminal for safety.")
        return False

    try:
        response = input("\nType 'approve' to apply this change (Enter or anything else rejects): ").strip().lower()
        if response == "approve":
            print("[+] Diff approved by user. Proceeding to apply.")
            return True
        else:
            print("[-] Diff rejected. No files were modified.")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n[-] Operation cancelled. No files were modified.")
        return False


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the run command."""
    workspace = Path(args.workspace).resolve()
    print_banner(str(workspace), args.preset, args.backend, args.scenario)

    if args.backend.lower() == "mock":
        adapter = MockModelAdapter(scenario=args.scenario)
    elif args.backend.lower() == "api":
        adapter = ApiModelAdapter()
    else:
        print(f"Error: Unsupported backend '{args.backend}'. Use 'mock' or 'api'.", file=sys.stderr)
        return 3

    report = execute_run(
        workspace=workspace,
        task=args.task,
        model_adapter=adapter,
        preset_name=args.preset,
        approval_callback=interactive_approval,
        timeout_override=args.timeout,
        confirmed_min=args.confirmed_min,
    )

    render_final_report(report)

    if report.state == RunState.REJECTED:
        return 3
    if report.verdict.state == "VERIFIED":
        return 0
    if report.verdict.state == "FAILED":
        return 1
    return 2


def cmd_revert(args: argparse.Namespace) -> int:
    """Execute the revert command."""
    workspace = Path(args.workspace).resolve()
    try:
        restored = revert_backup(workspace, run_id=args.run)
        print("=" * 70)
        print(f" REVERT COMPLETED FOR RUN ID: {args.run}")
        print("=" * 70)
        print(f"Restored {len(restored)} file(s) to exact pre-run state:")
        for r in restored:
            print(f"  * {r}")
        print("=" * 70)
        return 0
    except Exception as err:
        print(f"Revert failed: {err}", file=sys.stderr)
        return 3


def cmd_demo_reset(args: argparse.Namespace) -> int:
    """Execute the demo-reset command."""
    seed_dir = Path(args.seed).resolve()
    workspace_dir = Path(args.workspace).resolve()
    try:
        reset_demo(seed_dir, workspace_dir)
        print("=" * 70)
        print(" DEMO RESET SUCCESSFUL")
        print("=" * 70)
        print(f"Copied pristine seed from: {seed_dir}")
        print(f"Into working workspace:    {workspace_dir}")
        print("=" * 70)
        return 0
    except Exception as err:
        print(f"Demo reset failed: {err}", file=sys.stderr)
        return 3


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="devo",
        description="Devo: Evidence-first coding assistant CLI for Python projects.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_p = subparsers.add_parser("run", help="Run the evidence-first verification journey")
    run_p.add_argument("--workspace", "-w", required=True, help="Path to local target workspace")
    run_p.add_argument("--task", "-t", required=True, help="Bug fix or task description")
    run_p.add_argument("--preset", default="pytest", help="Check preset to run (default: pytest)")
    run_p.add_argument("--backend", default="mock", choices=["mock", "api"], help="Model backend (default: mock)")
    run_p.add_argument("--scenario", default="scenario_verified", help="Mock scenario fixture name (default: scenario_verified)")
    run_p.add_argument("--timeout", type=float, default=None, help="Check execution timeout override in seconds")
    run_p.add_argument("--confirmed-min", type=int, default=0, help="Minimum expected passing test count")

    # revert command
    revert_p = subparsers.add_parser("revert", help="Safely rollback changes made during a run")
    revert_p.add_argument("--run", "-r", required=True, help="Run ID to restore")
    revert_p.add_argument("--workspace", "-w", default=".", help="Path to local target workspace")

    # demo-reset command
    reset_p = subparsers.add_parser("demo-reset", help="Reset demo/workspace from demo/seed")
    reset_p.add_argument("--seed", default="demo/seed", help="Path to demo seed directory")
    reset_p.add_argument("--workspace", "-w", default="demo/workspace", help="Path to demo workspace directory")

    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "revert":
        return cmd_revert(args)
    elif args.command == "demo-reset":
        return cmd_demo_reset(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
