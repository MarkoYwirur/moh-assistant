from pathlib import Path
from typing import Any, Dict, List
import yaml


SOURCE_REGISTRY_PATH = Path(__file__).parent / "data" / "source_registry.yaml"
FAMILY_SOURCE_POLICY_PATH = Path(__file__).parent / "data" / "family_source_policy.yaml"


def load_source_registry() -> Dict[str, Any]:
    if not SOURCE_REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Source registry not found: {SOURCE_REGISTRY_PATH}")

    with SOURCE_REGISTRY_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Source registry must be a top-level object")

    return data


def load_family_source_policy() -> Dict[str, Any]:
    if not FAMILY_SOURCE_POLICY_PATH.exists():
        raise FileNotFoundError(f"Family source policy not found: {FAMILY_SOURCE_POLICY_PATH}")

    with FAMILY_SOURCE_POLICY_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Family source policy must be a top-level object")

    return data


def get_all_sources() -> List[Dict[str, Any]]:
    data = load_source_registry()
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("'sources' must be a list")
    return sources


def get_sources_for_family(family: str, approved_only: bool = True) -> List[Dict[str, Any]]:
    if not family or not isinstance(family, str):
        raise ValueError("family must be a non-empty string")

    matched = []
    for source in get_all_sources():
        family_tags = source.get("family_tags", []) or []
        if family not in family_tags:
            continue

        if approved_only and not source.get("approved_for_retrieval", False):
            continue

        matched.append(source)

    return matched


def get_allowed_source_ids_for_family(family: str) -> List[str]:
    if not family or not isinstance(family, str):
        raise ValueError("family must be a non-empty string")

    policy = load_family_source_policy()
    families = policy.get("families", {}) or {}
    family_cfg = families.get(family, {}) or {}
    allowed = family_cfg.get("allowed_source_ids", []) or []

    if not isinstance(allowed, list):
        raise ValueError("allowed_source_ids must be a list")

    return allowed


def get_effective_sources_for_family(family: str) -> List[Dict[str, Any]]:
    broad_sources = get_sources_for_family(family, approved_only=True)
    allowed_ids = set(get_allowed_source_ids_for_family(family))

    if not allowed_ids:
        return broad_sources

    filtered = [s for s in broad_sources if s.get("source_id") in allowed_ids]
    return filtered
