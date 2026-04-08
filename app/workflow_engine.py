from pathlib import Path
from typing import Any, Dict
import yaml


WORKFLOWS_DIR = Path(__file__).parent / "workflows"


def load_workflow_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Workflow file must contain a top-level object: {path}")

    return data


def get_workflow_by_family(family: str) -> Dict[str, Any]:
    if not family or not isinstance(family, str):
        raise ValueError("family must be a non-empty string")

    path = WORKFLOWS_DIR / f"{family}.yaml"
    return load_workflow_file(path)
