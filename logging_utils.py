import json
from datetime import datetime
from pathlib import Path

from app.issue_family_classifier import classify_issue_family, normalize_text_v2

LOG_DIR = Path(r"C:\Users\Asus\Desktop\moh-assistant\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
INTERNAL_DIR = Path(r"C:\Users\Asus\Desktop\moh-assistant\internal")

LOG_FILE = LOG_DIR / "requests.jsonl"
PHASE6_SHADOW_LOG_FILE = LOG_DIR / "phase6_shadow_disagreements.jsonl"
PHASE6_LIVE_PILOT_LOG_FILE = LOG_DIR / "phase6_live_pilot_events.jsonl"
PHASE6_LIVE_PILOT_CONFIG_FILE = INTERNAL_DIR / "phase6_live_pilot_config.json"

GENERIC_SPECIALIST_PROCESS_SURFACE_ID = "generic_specialist_process_residue"
NOISY_ADMISSION_TIMING_SURFACE_ID = "noisy_admission_timing_residue"
COMPLAINT_GENERIC_PROCEDURE_SURFACE_ID = "complaint_generic_procedure_residue"
DEFERRED_LEGAL_BASIS_SURFACE_ID = "deferred_legal_basis_vs_eligibility_overlap"

GENERIC_SPECIALIST_REFERRAL_NEEDED_BUCKET = "referral_needed"
GENERIC_SPECIALIST_ROUTING_ARRANGEMENT_BUCKET = "routing_arrangement"
GENERIC_SPECIALIST_FREE_CARE_COVERAGE_BUCKET = "free_care_coverage"
GENERIC_SPECIALIST_OTHER_BUCKET = "other"

GENERIC_SPECIALIST_NOUN_MARKERS = (
    "մասնագետ",
    "նեղ մասնագետ",
)

GENERIC_SPECIALIST_NAMED_MARKERS = (
    "սրտաբան",
    "նյարդաբան",
    "ակնաբույժ",
    "մաշկաբան",
    "գինեկոլոգ",
    "էնդոկրինոլոգ",
    "ուռոլոգ",
    "օրթոպեդ",
    "վիրաբույժ",
)

GENERIC_SPECIALIST_REFERRAL_STATUS_MARKERS = (
    "ուղեգիր է պետք",
    "ուղեգիր պետք է",
    "առանց ուղեգրի",
    "առանց ուղղեգրի",
    "ուղեգիր չունեմ",
    "ուղեգիր չունենալով",
)

GENERIC_SPECIALIST_ROUTING_MARKERS = (
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "որտեղ գնամ",
    "ուր գնամ",
    "ինչպես գրանցվեմ",
    "ինչպես հերթագրվեմ",
    "ինչ հարցով",
    "նախ բժիշկ պիտի տեսնե",
    "գնալու համար",
)

GENERIC_SPECIALIST_ELIGIBILITY_MARKERS = (
    "անվճար",
    "ծածկ",
    "պետպատվ",
    "արտոնյալ",
)

GENERIC_SPECIALIST_DISQUALIFIERS = (
    "մռտ",
    "mri",
    "կտ",
    "ct",
    "անալիզ",
    "հետազոտ",
    "լաբորատոր",
    "բողոք",
    "գանգատ",
    "հիվանդանոց",
    "վիրահատ",
)

NOISY_ADMISSION_TIMING_HOSPITAL_MARKERS = (
    "հիվանդանոց",
    "հոսպիտալ",
    "ստացիոնար",
)

NOISY_ADMISSION_TIMING_VERB_MARKERS = (
    "ընդուն",
    "պառկեցն",
    "հոսպիտալացն",
)

NOISY_ADMISSION_TIMING_TIMING_MARKERS = (
    "երբ",
    "ինչպես",
)

NOISY_ADMISSION_TIMING_PAYMENT_MARKERS = (
    "վճար",
    "գումար",
    "պետպատվ",
    "անվճար",
    "ծածկ",
    "պարտք",
)

NOISY_ADMISSION_TIMING_DISQUALIFIERS = (
    "ինչ է պետք",
    "ինչ փաստաթուղթ",
    "ինչ պայմաններով",
    "ինչ դեպքերում",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "բողոք",
    "գանգատ",
)

COMPLAINT_GENERIC_PROCEDURE_CORE_MARKERS = (
    "բողոք",
    "գանգատ",
)

COMPLAINT_GENERIC_PROCEDURE_PROCESS_MARKERS = (
    "ում դիմեմ",
    "որտեղ պետք է տամ",
    "որտեղ տամ",
    "ինչպես ընթացք տամ",
    "ինչպես ընթացք տալ",
    "ինչպես ներկայացնեմ",
)

COMPLAINT_GENERIC_PROCEDURE_DISQUALIFIERS = (
    "բուժաշխատող",
    "վնաս",
    "մերժ",
    "ուղեգիր",
    "դեղ",
    "վճար",
    "պարտք",
    "արմեդ",
    "տվյալ",
    "գրառում",
    "հերթ",
    "սպաս",
    "դեղատն",
    "հետազոտ",
    "անալիզ",
    "մռտ",
    "կտ",
    "պոլիկլինիկ",
    "գրանց",
    "կցագրվ",
    "ընտանեկան բժիշկ",
    "հիվանդանոց",
    "վիրահատ",
    "մասնագետ",
)

LEGAL_BASIS_MARKERS = (
    "իրավական",
    "իրավունք",
    "ակտ",
    "օրենք",
    "հիմք",
    "ամրագրվ",
    "կարգ",
    "կանոնակարգ",
)

LEGAL_BASIS_FREE_CARE_MARKERS = (
    "անվճար",
    "արտոնյալ",
    "բժշկական օգնություն",
    "բուժօգնություն",
    "պետպատվ",
)

LEGAL_BASIS_ELIGIBILITY_MARKERS = (
    "65+",
    "թոշակառու",
    "հաշմանդամ",
    "հղի",
    "երեխա",
    "սոցիալապես",
    "անապահով",
    "աշխատող",
    "ապահովագր",
    "ովքեր",
    "ով կարող է օգտվել",
)


def _map_runtime_card_to_shadow_family(matched_card_id: str | None) -> str | None:
    if not matched_card_id:
        return None

    if matched_card_id in {
        "eligibility_status_coverage_root_v1",
    }:
        return "eligibility_check"

    if matched_card_id in {
        "service_referral_status_root_v1",
        "routing_specialist_referral_confusion_v1",
        "routing_referral_where_to_go_v2",
        "service_family_doctor_route_curated",
    }:
        return "referral_specialist"

    if matched_card_id in {
        "service_admission_type_root_v1",
        "medicine_coverage_exact_name_dosage_form_v2",
    }:
        return "service_coverage_check"

    if matched_card_id in {
        "complaint_unexpected_payment_dispute_v2",
        "complaint_duplicate_charge_or_wrong_payment_status_v1",
    }:
        return "payment_dispute"

    if matched_card_id in {
        "complaint_2_official_complaint_channels",
    }:
        return "complaint_contact_help"

    if matched_card_id in {
        "complaint_missing_or_wrong_record_v1",
        "technical_armed_visibility_issue_v1",
    }:
        return "record_or_visibility_issue"

    if matched_card_id in {
        "complaint_medicine_not_provided_v1",
    }:
        return "medicine_not_provided"

    if matched_card_id in {
        "complaint_refusal_denied_service_v2",
    }:
        return "denied_service"

    return None


def _load_json_file(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def load_phase6_live_pilot_config() -> dict:
    default = {
        "artifact_type": "phase6_live_pilot_config",
        "mode": "bounded_live_pilot_control_plane",
        "surface_id": GENERIC_SPECIALIST_PROCESS_SURFACE_ID,
        "enabled": False,
        "allowlisted_families": [
            "service_referral_status_root_v1",
            "routing_specialist_referral_confusion_v1",
        ],
        "excluded_families": [
            "eligibility_status_coverage_root_v1",
        ],
        "eligible_buckets": [
            GENERIC_SPECIALIST_REFERRAL_NEEDED_BUCKET,
        ],
        "confidence_threshold": 0.45,
        "fallback_policy": "keep_runtime_winner",
        "kill_switch": True,
        "protected_neighbors": [
            "routing_specialist_referral_confusion_v1",
            "routing_referral_where_to_go_v2",
            "eligibility_status_coverage_root_v1",
        ],
        "rollback_thresholds": {
            "protected_neighbor_theft": 0,
            "regression_failures": 0,
            "release_blocking_benchmark_failures": 0,
            "reviewed_false_overrides": 0,
        },
    }
    return _load_json_file(PHASE6_LIVE_PILOT_CONFIG_FILE, default)


def append_request_log(payload: dict):
    message = str(payload.get("message", "") or "")
    matched_card_id = payload.get("matched_card_id")
    matched_family = payload.get("matched_family")
    follow_up_question = str(payload.get("follow_up_question", "") or "")

    shadow_family = classify_issue_family(message) if message else None
    runtime_family_proxy = _map_runtime_card_to_shadow_family(matched_card_id)
    if runtime_family_proxy is None and matched_family:
        runtime_family_proxy = str(matched_family)
    if (
        runtime_family_proxy is None
        and payload.get("action") == "partial_answer_with_clarify"
        and "որտեղ կամ ինչպես բողոք ներկայացնել" in follow_up_question
    ):
        runtime_family_proxy = "complaint_contact_help"

    row = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message_normalized": normalize_text_v2(message) if message else "",
        "shadow_family": shadow_family,
        "runtime_family_proxy": runtime_family_proxy,
        "shadow_family_agrees": (
            shadow_family == runtime_family_proxy
            if shadow_family and runtime_family_proxy
            else None
        ),
        **payload,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    shadow_rows = _build_phase6_shadow_rows(payload, runtime_family_proxy)
    for shadow_row in shadow_rows:
        with PHASE6_SHADOW_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(shadow_row, ensure_ascii=False) + "\n")

    pilot_event = evaluate_phase6_live_pilot(
        message=message,
        runtime_winner=payload.get("matched_card_id") or payload.get("matched_family"),
        runtime_family_proxy=runtime_family_proxy,
        action=payload.get("action"),
        follow_up_question=payload.get("follow_up_question"),
    )
    if pilot_event is not None:
        with PHASE6_LIVE_PILOT_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(pilot_event, ensure_ascii=False) + "\n")


def _build_phase6_shadow_rows(payload: dict, runtime_family_proxy: str | None) -> list[dict]:
    message = str(payload.get("message", "") or "")
    normalized = normalize_text_v2(message)
    if not normalized:
        return []

    rows = []
    surface_builders = (
        (_detect_generic_specialist_process_surface, _rank_generic_specialist_process_families),
        (_detect_noisy_admission_timing_surface, _rank_noisy_admission_timing_families),
        (_detect_complaint_generic_procedure_surface, _rank_complaint_generic_procedure_families),
        (_detect_deferred_legal_basis_surface, _rank_deferred_legal_basis_families),
    )

    for detector, ranker in surface_builders:
        surface = detector(normalized)
        if surface is None:
            continue

        ranking = ranker(normalized)
        if not ranking:
            continue

        total_score = sum(item["score"] for item in ranking)
        top_score = ranking[0]["score"]
        second_score = ranking[1]["score"] if len(ranking) > 1 else 0.0
        confidence = round((top_score - second_score) / total_score, 4) if total_score else 0.0

        rows.append(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "unresolved_surface_tag": surface,
                "original_user_text": message,
                "runtime_winner": payload.get("matched_card_id") or payload.get("matched_family"),
                "runtime_family_proxy": runtime_family_proxy,
                "shadow_predicted_family": ranking[0]["family_id"],
                "confidence": confidence,
                "competing_families": ranking,
                "action": payload.get("action"),
                "follow_up_question": payload.get("follow_up_question"),
            }
        )

    return rows


def _bucket_generic_specialist_process(normalized: str) -> str:
    if any(marker in normalized for marker in GENERIC_SPECIALIST_ELIGIBILITY_MARKERS):
        return GENERIC_SPECIALIST_FREE_CARE_COVERAGE_BUCKET
    if any(marker in normalized for marker in GENERIC_SPECIALIST_ROUTING_MARKERS):
        return GENERIC_SPECIALIST_ROUTING_ARRANGEMENT_BUCKET
    if any(marker in normalized for marker in GENERIC_SPECIALIST_REFERRAL_STATUS_MARKERS):
        return GENERIC_SPECIALIST_REFERRAL_NEEDED_BUCKET
    return GENERIC_SPECIALIST_OTHER_BUCKET


def evaluate_phase6_live_pilot(
    message: str,
    runtime_winner: str | None,
    runtime_family_proxy: str | None,
    action: str | None,
    follow_up_question: str | None,
    force_enabled: bool = False,
    ignore_kill_switch: bool = False,
) -> dict | None:
    normalized = normalize_text_v2(message)
    if not normalized:
        return None

    config = load_phase6_live_pilot_config()
    surface_id = str(config.get("surface_id") or "")
    if surface_id != GENERIC_SPECIALIST_PROCESS_SURFACE_ID:
        return None

    if _detect_generic_specialist_process_surface(normalized) is None:
        return None

    ranking = _rank_generic_specialist_process_families(normalized)
    if not ranking:
        return None

    total_score = sum(item["score"] for item in ranking)
    top_score = ranking[0]["score"]
    second_score = ranking[1]["score"] if len(ranking) > 1 else 0.0
    confidence = round((top_score - second_score) / total_score, 4) if total_score else 0.0
    shadow_family = ranking[0]["family_id"]
    bucket = _bucket_generic_specialist_process(normalized)

    allowlisted_families = list(config.get("allowlisted_families") or [])
    excluded_families = list(config.get("excluded_families") or [])
    eligible_buckets = list(config.get("eligible_buckets") or [])
    threshold = float(config.get("confidence_threshold") or 0.0)
    enabled = bool(config.get("enabled")) or force_enabled
    kill_switch = bool(config.get("kill_switch")) and not ignore_kill_switch

    override_eligible = False
    block_reason = "inactive_config"
    candidate_override_family = None

    if not enabled:
        block_reason = "pilot_disabled"
    elif kill_switch:
        block_reason = "kill_switch_active"
    elif bucket not in eligible_buckets:
        block_reason = "bucket_not_eligible"
    elif runtime_winner not in allowlisted_families:
        block_reason = "runtime_outside_allowlist"
    elif shadow_family not in allowlisted_families:
        block_reason = "shadow_outside_allowlist"
    elif shadow_family in excluded_families:
        block_reason = "shadow_family_excluded"
    elif confidence < threshold:
        block_reason = "low_confidence"
    elif runtime_winner == shadow_family:
        block_reason = "no_disagreement"
    else:
        override_eligible = True
        candidate_override_family = shadow_family
        block_reason = "eligible_but_not_applied"

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "surface_id": surface_id,
        "original_user_text": message,
        "runtime_winner": runtime_winner,
        "runtime_family_proxy": runtime_family_proxy,
        "shadow_predicted_family": shadow_family,
        "confidence": confidence,
        "bucket": bucket,
        "allowlisted_families": allowlisted_families,
        "excluded_families": excluded_families,
        "eligible_buckets": eligible_buckets,
        "fallback_policy": config.get("fallback_policy"),
        "pilot_enabled": enabled,
        "kill_switch": kill_switch,
        "override_eligible": override_eligible,
        "override_applied": False,
        "candidate_override_family": candidate_override_family,
        "block_reason": block_reason,
        "action": action,
        "follow_up_question": follow_up_question,
        "competing_families": ranking,
    }


def _detect_generic_specialist_process_surface(normalized: str) -> str | None:
    has_specialist_noun = any(marker in normalized for marker in GENERIC_SPECIALIST_NOUN_MARKERS)
    has_named_specialist = any(marker in normalized for marker in GENERIC_SPECIALIST_NAMED_MARKERS)
    has_disqualifier = any(marker in normalized for marker in GENERIC_SPECIALIST_DISQUALIFIERS)

    if has_specialist_noun and not has_named_specialist and not has_disqualifier:
        return GENERIC_SPECIALIST_PROCESS_SURFACE_ID

    return None


def _rank_generic_specialist_process_families(normalized: str) -> list[dict]:
    scores = {
        "service_referral_status_root_v1": 0.0,
        "routing_specialist_referral_confusion_v1": 0.0,
        "eligibility_status_coverage_root_v1": 0.0,
    }

    if any(marker in normalized for marker in GENERIC_SPECIALIST_REFERRAL_STATUS_MARKERS):
        scores["service_referral_status_root_v1"] += 3.0
    if "մասնագետի համար ուղեգիր" in normalized or "նեղ մասնագետի համար ուղեգիր" in normalized:
        scores["service_referral_status_root_v1"] += 2.0

    if any(marker in normalized for marker in GENERIC_SPECIALIST_ROUTING_MARKERS):
        scores["routing_specialist_referral_confusion_v1"] += 3.0
    if "ինչ է պետք" in normalized:
        scores["routing_specialist_referral_confusion_v1"] += 1.0

    if any(marker in normalized for marker in GENERIC_SPECIALIST_ELIGIBILITY_MARKERS):
        scores["eligibility_status_coverage_root_v1"] += 4.0

    ranking = [
        {"family_id": family_id, "score": round(score, 4)}
        for family_id, score in scores.items()
        if score > 0
    ]
    ranking.sort(key=lambda item: item["score"], reverse=True)
    return ranking


def _detect_noisy_admission_timing_surface(normalized: str) -> str | None:
    has_hospital_anchor = any(marker in normalized for marker in NOISY_ADMISSION_TIMING_HOSPITAL_MARKERS)
    has_timing_marker = any(marker in normalized for marker in NOISY_ADMISSION_TIMING_TIMING_MARKERS)
    has_admission_verb = any(marker in normalized for marker in NOISY_ADMISSION_TIMING_VERB_MARKERS)
    has_disqualifier = any(marker in normalized for marker in NOISY_ADMISSION_TIMING_DISQUALIFIERS)

    if has_hospital_anchor and has_timing_marker and has_admission_verb and not has_disqualifier:
        return NOISY_ADMISSION_TIMING_SURFACE_ID

    return None


def _rank_noisy_admission_timing_families(normalized: str) -> list[dict]:
    scores = {
        "service_admission_type_root_v1": 0.0,
        "complaint_unexpected_payment_dispute_v2": 0.0,
    }

    if any(marker in normalized for marker in NOISY_ADMISSION_TIMING_HOSPITAL_MARKERS):
        scores["service_admission_type_root_v1"] += 2.0
    if any(marker in normalized for marker in NOISY_ADMISSION_TIMING_VERB_MARKERS):
        scores["service_admission_type_root_v1"] += 2.0
    if "երբ" in normalized:
        scores["service_admission_type_root_v1"] += 1.0

    if any(marker in normalized for marker in NOISY_ADMISSION_TIMING_PAYMENT_MARKERS):
        scores["complaint_unexpected_payment_dispute_v2"] += 4.0
    if "չեն ընդունում" in normalized or "չեն պառկեցնում" in normalized:
        scores["complaint_unexpected_payment_dispute_v2"] += 1.0

    ranking = [
        {"family_id": family_id, "score": round(score, 4)}
        for family_id, score in scores.items()
        if score > 0
    ]
    ranking.sort(key=lambda item: item["score"], reverse=True)
    return ranking


def _detect_complaint_generic_procedure_surface(normalized: str) -> str | None:
    has_core_marker = any(marker in normalized for marker in COMPLAINT_GENERIC_PROCEDURE_CORE_MARKERS)
    has_process_marker = any(marker in normalized for marker in COMPLAINT_GENERIC_PROCEDURE_PROCESS_MARKERS)
    has_disqualifier = any(marker in normalized for marker in COMPLAINT_GENERIC_PROCEDURE_DISQUALIFIERS)

    if has_core_marker and has_process_marker and not has_disqualifier:
        return COMPLAINT_GENERIC_PROCEDURE_SURFACE_ID

    return None


def _rank_complaint_generic_procedure_families(normalized: str) -> list[dict]:
    scores = {
        "complaint_depth_mixed_intent_routing": 0.0,
        "routing_referral_where_to_go_v2": 0.0,
        "service_admission_type_root_v1": 0.0,
        "routing_specialist_referral_confusion_v1": 0.0,
    }

    if "գանգատ" in normalized or "բողոք" in normalized:
        scores["complaint_depth_mixed_intent_routing"] += 2.0
    if "ում դիմեմ" in normalized or "որտեղ պետք է տամ" in normalized:
        scores["complaint_depth_mixed_intent_routing"] += 1.0

    if "ուր" in normalized or "որտեղ" in normalized:
        scores["routing_referral_where_to_go_v2"] += 1.0

    ranking = [
        {"family_id": family_id, "score": round(score, 4)}
        for family_id, score in scores.items()
        if score > 0
    ]
    ranking.sort(key=lambda item: item["score"], reverse=True)
    return ranking


def _detect_deferred_legal_basis_surface(normalized: str) -> str | None:
    has_legal_anchor = any(marker in normalized for marker in LEGAL_BASIS_MARKERS)
    has_free_care_anchor = any(marker in normalized for marker in LEGAL_BASIS_FREE_CARE_MARKERS)

    if has_legal_anchor and has_free_care_anchor:
        return DEFERRED_LEGAL_BASIS_SURFACE_ID

    return None


def _rank_deferred_legal_basis_families(normalized: str) -> list[dict]:
    scores = {
        "info_rights_governance_legal_basis_v1": 0.0,
        "eligibility_status_coverage_root_v1": 0.0,
    }

    legal_anchor_count = sum(1 for marker in LEGAL_BASIS_MARKERS if marker in normalized)
    scores["info_rights_governance_legal_basis_v1"] += float(legal_anchor_count * 2)

    if "ովքեր" in normalized or "ով կարող է օգտվել" in normalized:
        scores["eligibility_status_coverage_root_v1"] += 2.0

    eligibility_marker_count = sum(1 for marker in LEGAL_BASIS_ELIGIBILITY_MARKERS if marker in normalized)
    scores["eligibility_status_coverage_root_v1"] += float(eligibility_marker_count)

    ranking = [
        {"family_id": family_id, "score": round(score, 4)}
        for family_id, score in scores.items()
        if score > 0
    ]
    ranking.sort(key=lambda item: item["score"], reverse=True)
    return ranking
