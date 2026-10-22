"""Backup and hash-verified revert management for safe state rollback."""
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from devo.workspace.boundary import resolve_safe_path


class RevertError(RuntimeError):
    """Raised when backup or revert integrity check fails."""
    pass


@dataclass
class BackupEntry:
    rel_path: str
    original_sha256: str
    backup_file: str


@dataclass
class BackupManifest:
    run_id: str
    entries: list[BackupEntry]


def compute_file_hash(path: Path) -> str:
    """Calculate SHA-256 hash of a file on disk."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_backup(
    workspace: Path | str,
    rel_files: list[str],
    run_id: str,
    runs_dir: Path | str = ".devo-runs",
) -> BackupManifest:
    """Backup original files to .devo-runs/<run-id>/backup/ and record SHA-256 hashes."""
    ws = Path(workspace).resolve()
    backup_root = (ws / runs_dir / run_id / "backup").resolve()
    backup_root.mkdir(parents=True, exist_ok=True)

    entries: list[BackupEntry] = []

    for rel in rel_files:
        src = resolve_safe_path(rel, ws)
        if not src.is_file():
            continue

        file_hash = compute_file_hash(src)
        dst = backup_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        entries.append(
            BackupEntry(
                rel_path=rel,
                original_sha256=file_hash,
                backup_file=str(dst.relative_to(backup_root)),
            )
        )

    manifest = BackupManifest(run_id=run_id, entries=entries)
    manifest_path = backup_root.parent / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(asdict(manifest), f, indent=2)

    return manifest


def revert_backup(
    workspace: Path | str,
    run_id: str,
    runs_dir: Path | str = ".devo-runs",
    force: bool = False,
) -> list[str]:
    """Restore backed up files for a run_id, verifying hashes before restoration."""
    ws = Path(workspace).resolve()
    run_dir = (ws / runs_dir / run_id).resolve()
    manifest_path = run_dir / "manifest.json"

    if not manifest_path.exists():
        raise RevertError(f"No backup manifest found for run ID: '{run_id}' at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    backup_root = run_dir / "backup"
    restored: list[str] = []

    for entry in data.get("entries", []):
        rel = entry["rel_path"]
        backup_file = backup_root / entry["backup_file"]
        target = resolve_safe_path(rel, ws)

        if not backup_file.exists():
            raise RevertError(f"Corrupt backup: missing backup file {backup_file}")

        # Verify integrity of the backup file itself against original hash
        if compute_file_hash(backup_file) != entry["original_sha256"]:
            raise RevertError(f"Backup file was altered: {backup_file}")

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, target)
        restored.append(rel)

    return restored
