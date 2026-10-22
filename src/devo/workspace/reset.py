"""Reset utility to restore demo workspace from seed."""
import shutil
from pathlib import Path


def reset_demo(seed_dir: Path | str, workspace_dir: Path | str) -> None:
    """Copy contents of seed_dir into workspace_dir cleanly."""
    seed_path = Path(seed_dir).resolve()
    workspace_path = Path(workspace_dir).resolve()

    if not seed_path.exists():
        raise FileNotFoundError(f"Seed directory does not exist: {seed_path}")

    if workspace_path.exists():
        shutil.rmtree(workspace_path)

    workspace_path.mkdir(parents=True, exist_ok=True)

    for item in seed_path.iterdir():
        dest = workspace_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
