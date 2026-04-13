import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from main import ChatRequest, chat


REPORT_PATH = ROOT / "phase6_pilot_benchmark_report.json"


CASES = [
    {"owner": "service_referral_status_root_v1", "message": "մռտ անվճա՞ր է"},
    {"owner": "service_referral_status_root_v1", "message": "կտ անվճա՞ր է"},
    {"owner": "service_referral_status_root_v1", "message": "անալիզի համար ուղեգիր է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "կտ-ի համար ուղեգիր է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "մռտ-ի համար ուղեգիր է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "սրտաբանի համար ուղեգիր է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "եթե ուղեգիր չունեմ սրտաբանի մոտ կընդունեն"},
    {"owner": "service_referral_status_root_v1", "message": "մռտ-ի համար ինչ փաստաթուղթ է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "համակարգչային տոմոգրաֆիայի համար ինչ է պետք"},
    {"owner": "service_referral_status_root_v1", "message": "առանց ուղեգրի մասնագետի մոտ կարո՞ղ եմ գնալ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "ուր դիմեմ ուղեգիր ստանալու համար"},
    {"owner": "routing_referral_where_to_go_v2", "message": "մռտ-ի համար ուր դիմեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "կտ-ի համար ուր դիմեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "անալիզի համար ուր դիմեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "հետազոտության համար ուր դիմեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "մռտ-ի համար ինչպես գրանցվեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "կտ-ի համար ինչպես գրանցվեմ"},
    {"owner": "routing_referral_where_to_go_v2", "message": "որտեղ դիմեմ մռտ անելու համար"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "նեղ մասնագետի ուղեգիր է պետք"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "մասնագետի մոտ ինչպես գնամ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "մասնագետի համար նախ բժիշկ պիտի տեսնե՞մ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "մասնագետի մոտ ինչպես գրանցվեմ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "մասնագետի մոտ ինչպես հերթագրվեմ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "նեղ մասնագետի համար ուր դիմեմ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "ինչպես են ընդունում մասնագետի մոտ"},
    {"owner": "routing_specialist_referral_confusion_v1", "message": "մասնագետի մոտ գնալու համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "Հիվանդանոց ընդունվելու կարգը որն է"},
    {"owner": "service_admission_type_root_v1", "message": "ստացիոնար ընդունվելու համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "պլանային ընդունում է թե անհետաձգելի"},
    {"owner": "service_admission_type_root_v1", "message": "հիվանդանոց պառկելու համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "ինչպես հոսպիտալացվեմ"},
    {"owner": "service_admission_type_root_v1", "message": "ինչպես պառկեմ հիվանդանոց"},
    {"owner": "service_admission_type_root_v1", "message": "հոսպիտալացման համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "պլանային հոսպիտալացման համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "վիրահատության համար ինչ է պետք"},
    {"owner": "service_admission_type_root_v1", "message": "ինչ դեպքերում են հոսպիտալացնում"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "ովքեր կարող են օգտվել պետպատվերից"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "ովքեր ունեն անվճար բուժօգնության իրավունք"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "ո՞վ կարող է օգտվել արտոնյալ բուժօգնությունից"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "մասնագետի մոտ անվճար կարո՞ղ եմ գնալ"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "ես շահառու եմ թե ոչ"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "պետպատվերից ո՞վ կարող է օգտվել"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "հղիներին անվճար բուժօգնություն հասնու՞մ է"},
    {"owner": "eligibility_status_coverage_root_v1", "message": "զինվորական ընտանիքը պետպատվեր ունի՞"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "ինձ մերժել են ու չեն սպասարկել"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե ծառայությունը մերժել են ուր դիմեմ բողոքով"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե ուղեգիր չեն տալիս որտեղ բողոքեմ"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե անալիզ չեն արել որտեղ բողոքեմ"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե չեմ կարող կցագրվել ընտանեկան բժշկի մոտ ուր դիմեմ"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե ուրիշ պոլիկլինիկա չեմ կարող գրանցվել ուր դիմեմ"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Հետազոտությունը չեն արել ուր դիմեմ բողոքով"},
    {"owner": "complaint_refusal_denied_service_v2", "message": "Եթե մռտ-ի համար չեն ընդունել ուր դիմեմ բողոքով"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Ուր զանգեմ բողոքի համար"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Որտեղ բողոք ներկայացնեմ"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Ինչպես կապվել բողոքի համար"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Բողոքով ում պետք է դիմեմ"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Ում դիմեմ գանգատով"},
    {"owner": "complaint_2_official_complaint_channels", "message": "Որտեղ պետք է դիմեմ բողոքով"},
    {"owner": "complaint_29_inspection", "message": "Եթե երկար հերթ է եղել որտեղ բողոքեմ"},
    {"owner": "complaint_29_inspection", "message": "Սպասման ժամից դժգոհ եմ ուր դիմեմ բողոքով"},
    {"owner": "complaint_29_inspection", "message": "Եթե դեղատնից դժգոհ եմ որտեղ բողոքեմ"},
    {"owner": "complaint_29_inspection", "message": "Դեղատան սպասարկման համար ուր դիմեմ բողոքով"},
    {"owner": "complaint_29_inspection", "message": "Հիվանդանոցի ծառայության համար ուր դիմեմ բողոքով"},
    {"owner": "complaint_29_inspection", "message": "Հերթից բողոք ունեմ որտեղ դիմեմ"},
    {"owner": "complaint_40_provider_misconduct", "message": "Բուժաշխատողի վարքից բողոք ունեմ"},
    {"owner": "complaint_40_provider_misconduct", "message": "Բժշկի վարքագծից ուր բողոքեմ"},
    {"owner": "complaint_40_provider_misconduct", "message": "Բժիշկը կոպիտ է եղել որտեղ բողոքեմ"},
    {"owner": "complaint_40_provider_misconduct", "message": "Բուժաշխատողի էթիկայի խախտման համար ուր դիմեմ"},
    {"owner": "complaint_40_provider_misconduct", "message": "Մեդաշխատողի ոչ պատշաճ վարքի մասին որտեղ բողոքեմ"},
    {"owner": "complaint_duplicate_charge_or_wrong_payment_status_v1", "message": "երկու անգամ են գանձել"},
    {"owner": "complaint_duplicate_charge_or_wrong_payment_status_v1", "message": "վճարման կարգավիճակը սխալ է"},
    {"owner": "complaint_duplicate_charge_or_wrong_payment_status_v1", "message": "երկու անգամ վճար եմ արել"},
    {"owner": "complaint_duplicate_charge_or_wrong_payment_status_v1", "message": "վճարել եմ բայց համակարգում չի նստել"},
    {"owner": "complaint_duplicate_charge_or_wrong_payment_status_v1", "message": "սխալ վճարման կարգավիճակ է երևում"},
    {"owner": "complaint_missing_or_wrong_record_v1", "message": "գրառում չկա"},
    {"owner": "complaint_missing_or_wrong_record_v1", "message": "տվյալը սխալ է երևում"},
    {"owner": "complaint_missing_or_wrong_record_v1", "message": "էլեկտրոնային գրառումը բացակայում է"},
    {"owner": "complaint_missing_or_wrong_record_v1", "message": "իմ տվյալները սխալ են լրացրել"},
    {"owner": "complaint_missing_or_wrong_record_v1", "message": "բժշկական գրառումս սխալ է"},
    {"owner": "complaint_medicine_not_provided_v1", "message": "դեղը չեն տվել"},
    {"owner": "complaint_medicine_not_provided_v1", "message": "անվճար դեղը չեն տրամադրել"},
    {"owner": "complaint_medicine_not_provided_v1", "message": "դեղատանը դեղը չեն տվել"},
    {"owner": "complaint_medicine_not_provided_v1", "message": "ասացին դեղը չկա ու չեն տալիս"},
    {"owner": "complaint_medicine_not_provided_v1", "message": "պետական ծրագրով դեղը չեն տվել"},
    {"owner": "medicine_coverage_exact_name_dosage_form_v2", "message": "էս դեղը պետությունը տալիս ա՞"},
    {"owner": "medicine_coverage_exact_name_dosage_form_v2", "message": "պարացետամոլ 500 մգ հաբը ծածկվո՞ւմ է"},
    {"owner": "medicine_coverage_exact_name_dosage_form_v2", "message": "ինսուլինը պետպատվերով տալի՞ս են"},
    {"owner": "medicine_coverage_exact_name_dosage_form_v2", "message": "այս դեղը անվճա՞ր է"},
    {"owner": "medicine_coverage_exact_name_dosage_form_v2", "message": "դեղի ծածկույթը ուզում եմ ճշտել"},
    {"owner": "technical_armed_visibility_issue_v1", "message": "արմեդում չի երևում"},
    {"owner": "technical_armed_visibility_issue_v1", "message": "Եթե ԱՐՄԵԴ-ում չի երևում որտեղ բողոքեմ"},
    {"owner": "technical_armed_visibility_issue_v1", "message": "Արմեդում դեղատոմսը չի երևում"},
    {"owner": "technical_armed_visibility_issue_v1", "message": "Արմեդում գրառումը բացակայում է"},
    {"owner": "technical_armed_visibility_issue_v1", "message": "Արմեդը ցույց չի տալիս տվյալները"},
    {"owner": "faq_27", "message": "Ի՞նչ պատասխանատվություն են կրում բժշկական օգնություն իրականացնողները իրենց մեղքով վնաս պատճառելու դեպքում"},
    {"owner": "faq_27", "message": "Բժշկի մեղքով վնասի դեպքում ինչ պատասխանատվություն կա"},
    {"owner": "faq_39", "message": "Ինչպե՞ս գրանցվել ընտանեկան բժշկի մոտ"},
    {"owner": "faq_39", "message": "Պոլիկլինիկա փոխելու կարգը որն է"},
    {"owner": "faq_39", "message": "Կարո՞ղ եմ փոխել իմ ընտանեկան բժշկին"},
    {"owner": "faq_40", "message": "Ե՞րբ կարող է ընտանեկան բժիշկը հրաժարվել գրանցելուց"},
    {"owner": "faq_40", "message": "Ինչ պատճառներով կարող են հրաժարվել կցագրելուց"},
]


def run_case(message: str) -> dict:
    response = chat(ChatRequest(message=message, state=None))
    return {
        "action": response.get("action"),
        "matched_card_id": response.get("matched_card_id"),
        "follow_up_question": response.get("follow_up_question"),
    }


def owner_matches(expected_owner: str, actual_owner: str | None) -> bool:
    if actual_owner is None:
        return False
    if actual_owner == expected_owner:
        return True
    if expected_owner.startswith("faq_"):
        return actual_owner.startswith(expected_owner)
    return False


def main() -> None:
    owner_counts = Counter()
    owner_passes = Counter()
    failures = []
    results = []

    for case in CASES:
        outcome = run_case(case["message"])
        passed = owner_matches(case["owner"], outcome["matched_card_id"])
        owner_counts[case["owner"]] += 1
        if passed:
            owner_passes[case["owner"]] += 1
        else:
            failures.append(
                {
                    "message": case["message"],
                    "expected_owner": case["owner"],
                    "actual_owner": outcome["matched_card_id"],
                    "action": outcome["action"],
                    "follow_up_question": outcome["follow_up_question"],
                }
            )
        results.append(
            {
                "message": case["message"],
                "expected_owner": case["owner"],
                "actual_owner": outcome["matched_card_id"],
                "action": outcome["action"],
                "passed": passed,
            }
        )

    per_owner = []
    for owner, total in sorted(owner_counts.items()):
        passed = owner_passes[owner]
        per_owner.append(
            {
                "owner": owner,
                "passed": passed,
                "total": total,
                "accuracy": round(passed / total, 4),
            }
        )

    score = round((len(CASES) - len(failures)) / len(CASES), 4)
    report = {
        "suite_name": "phase6_pilot_readiness_benchmark",
        "case_count": len(CASES),
        "passed": len(CASES) - len(failures),
        "failed": len(failures),
        "accuracy": score,
        "rating": (
            "ready_for_shadow_pilot_review"
            if score >= 0.95
            else "needs_more_work_before_pilot_review"
        ),
        "per_owner": per_owner,
        "failures": failures,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "case_count": report["case_count"],
        "passed": report["passed"],
        "failed": report["failed"],
        "accuracy": report["accuracy"],
        "rating": report["rating"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
