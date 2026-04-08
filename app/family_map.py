from pathlib import Path
from typing import Any, Dict
import yaml


V2_FAMILY_MAP_PATH = Path(__file__).parent / "data" / "v2_family_map.yaml"


def load_v2_family_map() -> Dict[str, Any]:
    if not V2_FAMILY_MAP_PATH.exists():
        raise FileNotFoundError(f"V2 family map not found: {V2_FAMILY_MAP_PATH}")

    with V2_FAMILY_MAP_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("V2 family map must be a top-level object")

    return data


def get_all_family_configs() -> Dict[str, Any]:
    data = load_v2_family_map()
    families = data.get("families", {})
    if not isinstance(families, dict):
        raise ValueError("'families' must be an object")
    return families


def get_family_config(family: str) -> Dict[str, Any]:
    if not family or not isinstance(family, str):
        raise ValueError("family must be a non-empty string")

    families = get_all_family_configs()
    cfg = families.get(family)

    if not isinstance(cfg, dict):
        raise KeyError(f"Family config not found: {family}")

    return cfg
