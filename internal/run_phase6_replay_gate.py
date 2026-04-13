import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from main import ChatRequest, chat
from logging_utils import (
    GENERIC_SPECIALIST_PROCESS_SURFACE_ID,
    evaluate_phase6_live_pilot,
)


DATASET_PATH = ROOT / "phase6_generic_specialist_reviewed_dataset.json"
LOG_PATH = ROOT.parent / "logs" / "phase6_shadow_disagreements.jsonl"
REPORT_PATH = ROOT / "phase6_generic_specialist_replay_gate_report.json"


def load_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def load_shadow_rows() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("unresolved_surface_tag") == GENERIC_SPECIALIST_PROCESS_SURFACE_ID:
            rows.append(row)
    return rows


def run_dataset_case(message: str) -> dict:
    response = chat(ChatRequest(message=message, state=None))
    runtime_winner = response.get("matched_card_id")
    pilot_eval = evaluate_phase6_live_pilot(
        message=message,
        runtime_winner=runtime_winner,
        runtime_family_proxy=None,
        action=response.get("action"),
        follow_up_question=response.get("follow_up_question"),
        force_enabled=True,
        ignore_kill_switch=True,
    )
    return {
        "response": response,
        "pilot_eval": pilot_eval,
    }


def bucket_shadow_history(rows: list[dict]) -> dict:
    bucket_counts = Counter()
    disagreement_counts = Counter()
    for row in rows:
        bucket = row.get("bucket")
        if not bucket:
            pilot_eval = evaluate_phase6_live_pilot(
                message=str(row.get("original_user_text") or ""),
                runtime_winner=row.get("runtime_winner"),
                runtime_family_proxy=row.get("runtime_family_proxy"),
                action=row.get("action"),
                follow_up_question=row.get("follow_up_question"),
                force_enabled=True,
                ignore_kill_switch=True,
            )
            bucket = pilot_eval.get("bucket") if pilot_eval else None
        if not bucket:
            continue
        bucket_counts[bucket] += 1
        runtime_winner = row.get("runtime_winner")
        shadow_family = row.get("shadow_predicted_family")
        if runtime_winner != shadow_family:
            disagreement_counts[bucket] += 1

    return {
        bucket: {
            "shadow_rows": bucket_counts[bucket],
            "runtime_shadow_disagreements": disagreement_counts[bucket],
        }
        for bucket in sorted(bucket_counts)
    }


def main() -> None:
    dataset = load_dataset()
    shadow_rows = load_shadow_rows()

    bucket_totals = Counter()
    bucket_runtime_correct = Counter()
    bucket_shadow_correct = Counter()
    bucket_disagreements = Counter()
    bucket_override_count = Counter()
    bucket_false_override_count = Counter()
    bucket_neighbor_theft_count = Counter()
    reviewed_results = []

    total_overrides = 0
    true_positive_overrides = 0
    false_overrides = 0

    for case in dataset["cases"]:
        message = case["message"]
        bucket = case["bucket"]
        gold_family = case["gold_family"]
        runtime = run_dataset_case(message)
        response = runtime["response"]
        pilot_eval = runtime["pilot_eval"] or {}

        runtime_winner = response.get("matched_card_id")
        shadow_family = pilot_eval.get("shadow_predicted_family")
        candidate_override = pilot_eval.get("candidate_override_family")
        override_eligible = bool(pilot_eval.get("override_eligible"))

        bucket_totals[bucket] += 1
        if runtime_winner == gold_family:
            bucket_runtime_correct[bucket] += 1
        if shadow_family == gold_family:
            bucket_shadow_correct[bucket] += 1
        if runtime_winner != shadow_family:
            bucket_disagreements[bucket] += 1

        if override_eligible:
            bucket_override_count[bucket] += 1
            total_overrides += 1
            if candidate_override == gold_family:
                true_positive_overrides += 1
            else:
                false_overrides += 1
                bucket_false_override_count[bucket] += 1

        if bucket != "referral_needed" and override_eligible:
            bucket_neighbor_theft_count[bucket] += 1

        reviewed_results.append(
            {
                "bucket": bucket,
                "message": message,
                "gold_family": gold_family,
                "runtime_winner": runtime_winner,
                "shadow_predicted_family": shadow_family,
                "shadow_confidence": pilot_eval.get("confidence"),
                "override_eligible": override_eligible,
                "candidate_override_family": candidate_override,
                "block_reason": pilot_eval.get("block_reason"),
            }
        )

    possible_repairs = sum(
        1
        for row in reviewed_results
        if row["runtime_winner"] != row["gold_family"]
    )
    precision = round(true_positive_overrides / total_overrides, 4) if total_overrides else 0.0
    recall = round(true_positive_overrides / possible_repairs, 4) if possible_repairs else 0.0

    bucket_breakdown = {}
    for bucket in sorted(bucket_totals):
        total = bucket_totals[bucket]
        runtime_correct = bucket_runtime_correct[bucket]
        shadow_correct = bucket_shadow_correct[bucket]
        disagreements = bucket_disagreements[bucket]
        overrides = bucket_override_count[bucket]
        false_override_count = bucket_false_override_count[bucket]
        neighbor_theft_count = bucket_neighbor_theft_count[bucket]
        bucket_breakdown[bucket] = {
            "reviewed_rows": total,
            "runtime_correct": runtime_correct,
            "runtime_accuracy": round(runtime_correct / total, 4),
            "shadow_correct": shadow_correct,
            "shadow_accuracy": round(shadow_correct / total, 4),
            "disagreement_rate": round(disagreements / total, 4),
            "override_count": overrides,
            "false_override_count": false_override_count,
            "neighbor_theft_count": neighbor_theft_count,
        }

    report = {
        "artifact_type": "phase6_replay_gate_report",
        "surface_id": GENERIC_SPECIALIST_PROCESS_SURFACE_ID,
        "mode": "offline_reviewed_replay_only",
        "shadow_history": {
            "rows_reviewed": len(shadow_rows),
            "bucket_summary": bucket_shadow_history(shadow_rows),
        },
        "reviewed_dataset": {
            "path": str(DATASET_PATH).replace("\\", "/"),
            "reviewed_rows": len(reviewed_results),
            "bucket_breakdown": bucket_breakdown,
        },
        "candidate_override_metrics": {
            "total_reviewed_rows": len(reviewed_results),
            "disagreement_rate": round(
                sum(1 for row in reviewed_results if row["runtime_winner"] != row["shadow_predicted_family"]) / len(reviewed_results),
                4,
            ) if reviewed_results else 0.0,
            "precision": precision,
            "recall": recall,
            "override_count": total_overrides,
            "false_override_count": false_overrides,
            "neighbor_theft_count": sum(bucket_neighbor_theft_count.values()),
        },
        "reviewed_results": reviewed_results,
        "go_live_pilot": False,
        "why_not": [
            "The replay gate remains advisory because the control plane is still disabled and kill-switched.",
            "A live pilot would require zero neighbor theft in excluded buckets and stronger replay-backed improvement on referral_needed only.",
        ],
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "surface_id": report["surface_id"],
                "reviewed_rows": report["reviewed_dataset"]["reviewed_rows"],
                "precision": report["candidate_override_metrics"]["precision"],
                "recall": report["candidate_override_metrics"]["recall"],
                "override_count": report["candidate_override_metrics"]["override_count"],
                "false_override_count": report["candidate_override_metrics"]["false_override_count"],
                "neighbor_theft_count": report["candidate_override_metrics"]["neighbor_theft_count"],
                "go_live_pilot": report["go_live_pilot"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
