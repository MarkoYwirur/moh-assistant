import json
from pathlib import Path

BASE = Path(r"C:\Users\Asus\Desktop\moh-assistant")
KB = BASE / "kb"


def load_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, "list"
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        return data["cards"], "dict"
    raise ValueError(f"Unsupported JSON structure in {path}")


def save_json(path: Path, cards, mode: str):
    if mode == "list":
        payload = cards
    else:
        payload = {"cards": cards}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_card(path: Path, new_card: dict):
    cards, mode = load_json(path)
    replaced = False

    for i, card in enumerate(cards):
        if card.get("id") == new_card["id"]:
            cards[i] = new_card
            replaced = True
            break

    if not replaced:
        cards.append(new_card)

    save_json(path, cards, mode)
    print(f"UPDATED {path.name}: {new_card['id']}")


ct_card = {
    "id": "service_ct_policy_curated_v2",
    "category": "service_coverage",
    "patterns": [
        "կտ",
        "ct",
        "համակարգչային տոմոգրաֆիա",
        "կոմպյուտերային տոմոգրաֆիա",
        "ct scan"
    ],
    "approved_answer": "ԿՏ ծառայության պատասխանը կախված է ուղեգրի և կիրառվող պայմանների առկայությունից։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "referral_status"
    ],
    "field_questions": {
        "referral_status": "Ուղեգիր ունե՞ք։"
    },
    "field_values": {
        "referral_status": {
            "has_referral": [
                "այո",
                "ունեմ",
                "կա",
                "ուղեգիր ունեմ"
            ],
            "no_referral": [
                "ոչ",
                "չունեմ",
                "չկա",
                "ուղեգիր չունեմ"
            ]
        }
    },
    "answer_rules": [
        {
            "when": {
                "referral_status": "has_referral"
            },
            "answer": "Եթե ունեք ուղեգիր, ԿՏ ծառայության կազմակերպման և ծածկույթի հարցը պետք է գնահատվի գործող պայմաններով և համապատասխան բուժհաստատության կարգով։",
            "next_step": "Դիմեք ձեր բժշկին կամ այն բուժհաստատությանը, որտեղ պետք է իրականացվի հետազոտությունը, որպեսզի ճշտվի ծառայության կազմակերպման կարգը։"
        },
        {
            "when": {
                "referral_status": "no_referral"
            },
            "answer": "Եթե ուղեգիր չունեք, միայն այս տեղեկությամբ հնարավոր չէ հաստատել ԿՏ ծառայության ծածկույթը։",
            "next_step": "Նախ դիմեք ձեր պոլիկլինիկա կամ բուժող բժշկին՝ ուղեգրի անհրաժեշտությունը և հետագա կարգը ճշտելու համար։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "ԿՏ-ի պատասխանը կախված է ուղեգրի և ծառայության պայմաններից։",
    "next_step_if_missing": "Նախ պետք է պարզել՝ ուղեգիր ունե՞ք։",
    "priority": 100
}

medicine_card = {
    "id": "medicine_coverage_exact_name_dosage_form_v2",
    "category": "medicines",
    "patterns": [
        "դեղը պետությունը տալիս ա",
        "դեղը ծածկվում է",
        "դեղը անվճար է",
        "դեղորայքը անվճար է",
        "medicine covered",
        "medicine free",
        "պետությունը տալիս ա"
    ],
    "approved_answer": "Դեղորայքի ծածկույթի պատասխանը կախված է դեղի ճշգրիտ անվանումից, դեղաչափից և ձևից։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "medicine_name_details"
    ],
    "field_questions": {
        "medicine_name_details": "Գրեք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը։ Օրինակ՝ հաբ, սրվակ, 250 մգ։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "medicine_name_details": "__any__"
            },
            "answer": "Միայն ընդհանուր անվանումով հնարավոր չէ հաստատել դեղի ծածկույթը, քանի որ նշանակություն ունի ճշգրիտ անվանումը, դեղաչափը և ձևը։",
            "next_step": "Գրեք դեղի ամբողջական տվյալները, որպեսզի ստուգումը արվի ճիշտ համընկնմամբ։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Դեղորայքի ծածկույթը չի կարելի հաստատել միայն ընդհանուր հարցով։ Պետք է ճշգրիտ համընկնում անվանման, դեղաչափի և ձևի միջև։",
    "next_step_if_missing": "Նախ գրեք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը։",
    "priority": 100
}

payment_card = {
    "id": "complaint_unexpected_payment_dispute_v2",
    "category": "complaints",
    "patterns": [
        "գումար ուզել են",
        "վճար են պահանջել",
        "ասել են անվճար չի",
        "համավճար",
        "պետք է վճարեմ",
        "paid unexpectedly",
        "co pay",
        "payment dispute"
    ],
    "approved_answer": "Վճարի հարցում կարևոր է պարզել՝ խոսքը որ ծառայության մասին է և որտեղ է այն պահանջվել։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "service_context"
    ],
    "field_questions": {
        "service_context": "Ո՞ր ծառայության համար և որտե՞ղ են գումար պահանջել։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "service_context": "__any__"
            },
            "answer": "Միայն այն տեղեկությամբ, որ գումար են պահանջել, հնարավոր չէ վերջնական ասել՝ պահանջը ճիշտ էր, թե ոչ։",
            "next_step": "Նշեք ծառայության տեսակը և բուժհաստատությունը։ Եթե հարցը վերաբերում է հնարավոր խախտման կամ ոչ հստակ վճարի, պետք է դիմել բուժհաստատությանը պարզաբանման համար, իսկ անհրաժեշտության դեպքում՝ բողոքի կարգով։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Վճարի հարցերում նախ պետք է տարբերել՝ սա պաշտոնական վճար էր, համավճար, թե ոչ հիմնավորված պահանջ։",
    "next_step_if_missing": "Նախ գրեք՝ որ ծառայության համար և որտեղ են գումար պահանջել։",
    "priority": 100
}

routing_card = {
    "id": "routing_referral_where_to_go_v2",
    "category": "routing",
    "patterns": [
        "ուր դիմեմ",
        "որտեղ գնամ",
        "որ բժիշկի գնամ",
        "ուղեգիր որտեղից ստանամ",
        "որտեղ ստանամ ուղեգիր",
        "where should i go",
        "where do i get a referral"
    ],
    "approved_answer": "Ճիշտ ուղղորդումը կախված է նրանից՝ խոսքը ծառայության, հետազոտության, թե մասնագետի դիմելու մասին է։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "routing_need_type"
    ],
    "field_questions": {
        "routing_need_type": "Խոսքը ո՞ր տարբերակի մասին է՝ մասնագետ, հետազոտություն, թե ընդհանուր բուժօգնություն։"
    },
    "field_values": {
        "routing_need_type": {
            "specialist": [
                "մասնագետ",
                "նեղ մասնագետ",
                "specialist"
            ],
            "diagnostic": [
                "հետազոտություն",
                "մռտ",
                "կտ",
                "անալիզ",
                "diagnostic"
            ],
            "general_care": [
                "ընդհանուր",
                "բժիշկ",
                "պոլիկլինիկա",
                "general"
            ]
        }
    },
    "answer_rules": [
        {
            "when": {
                "routing_need_type": "specialist"
            },
            "answer": "Եթե խոսքը նեղ մասնագետի դիմելու մասին է, առաջին քայլը սովորաբար ձեր պոլիկլինիկա կամ ընտանեկան բժշկին դիմելն է, որպեսզի պարզվի՝ անհրաժեշտ է ուղեգիր, թե ոչ։",
            "next_step": "Դիմեք ձեր պոլիկլինիկա կամ ընտանեկան բժշկին՝ հաջորդ քայլը ճշտելու համար։"
        },
        {
            "when": {
                "routing_need_type": "diagnostic"
            },
            "answer": "Եթե խոսքը հետազոտության մասին է, ճիշտ ուղին կախված է հետազոտության տեսակից և ուղեգրի պահանջից։",
            "next_step": "Նախ պարզեք՝ տվյալ հետազոտության համար ուղեգիր պե՞տք է, և դրա համար դիմեք ձեր բժշկին կամ պոլիկլինիկա։"
        },
        {
            "when": {
                "routing_need_type": "general_care"
            },
            "answer": "Եթե հարցը ընդհանուր բուժօգնության մասին է, առաջին քայլը պոլիկլինիկա կամ ընտանեկան բժիշկ դիմելն է։",
            "next_step": "Դիմեք ձեր պոլիկլինիկա կամ ընտանեկան բժշկին՝ հետագա ուղղորդման համար։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Ուղղորդումը կախված է նրանից՝ խոսքը մասնագետի, հետազոտության, թե ընդհանուր բուժօգնության մասին է։",
    "next_step_if_missing": "Նախ գրեք՝ ինչի համար եք ուզում դիմել։",
    "priority": 100
}

refusal_card = {
    "id": "complaint_refusal_denied_service_v2",
    "category": "complaints",
    "patterns": [
        "մերժել են",
        "չեն սպասարկել",
        "ծառայությունը չեն տվել",
        "չեն ընդունել",
        "բողոք",
        "denied service",
        "refused care"
    ],
    "approved_answer": "Մերժման դեպքում նախ պետք է հասկանալ՝ խոսքը կազմակերպչական, ծածկույթի, թե վարքագծային խնդրի մասին է։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "refusal_context"
    ],
    "field_questions": {
        "refusal_context": "Ի՞նչ ծառայություն են մերժել կամ ինչո՞ւ չեն սպասարկել։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "refusal_context": "__any__"
            },
            "answer": "Միայն այն տեղեկությամբ, որ մերժել են, հնարավոր չէ վերջնական ասել՝ դա ծածկույթի, կազմակերպման, թե խախտման հարց է։",
            "next_step": "Գրեք՝ ինչ ծառայություն է եղել, որտեղ է եղել, և ինչ հիմնավորում են տվել։ Այդ տեղեկությունից հետո պետք է որոշել՝ հարցը լուծվում է պարզաբանմամբ, ուղղորդմամբ, թե բողոքով։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Մերժման հարցերում նախ պետք է պարզել՝ ինչ ծառայության մասին է խոսքը և ինչ հիմքով են մերժել։",
    "next_step_if_missing": "Նախ գրեք՝ ինչ ծառայություն են մերժել և ինչ պատճառ են ասել։",
    "priority": 100
}

upsert_card(KB / "service_coverage.json", ct_card)
upsert_card(KB / "medicines.json", medicine_card)
upsert_card(KB / "complaints.json", payment_card)
upsert_card(KB / "routing.json", routing_card)
upsert_card(KB / "complaints.json", refusal_card)

print("DONE")
