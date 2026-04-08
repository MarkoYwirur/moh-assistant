import json
from pathlib import Path

BASE = Path(r"C:\Users\Asus\Desktop\moh-assistant")
KB = BASE / "kb"


def load_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data, "list"
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        return data["cards"], "dict"
    raise ValueError(f"Unsupported JSON structure in {path}")


def save_json(path: Path, cards, mode: str):
    payload = cards if mode == "list" else {"cards": cards}
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


medicine_not_provided = {
    "id": "complaint_medicine_not_provided_v1",
    "category": "complaints",
    "patterns": [
        "դեղը չեն տվել",
        "դեղը չտվեցին",
        "դեղը չկա",
        "չեն տրամադրել դեղը",
        "դեղը չեն տալիս",
        "չեմ ստացել դեղը",
        "prescribed medicine not provided",
        "medicine not provided"
    ],
    "approved_answer": "Այս դեպքում նախ պետք է հստակեցնել՝ որ դեղի մասին է խոսքը և որտեղ այն չեն տրամադրել։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "medicine_name_details",
        "dispense_location"
    ],
    "field_questions": {
        "medicine_name_details": "Նշե՛ք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը։",
        "dispense_location": "Նշե՛ք՝ որտեղ չեն տրամադրել դեղը։ Օրինակ՝ դեղատուն, բուժհաստատություն կամ այլ կետ։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "medicine_name_details": "__any__",
                "dispense_location": "__any__"
            },
            "answer": "Եթե դեղը չեն տրամադրել, միայն այդ տեղեկությամբ դեռ հնարավոր չէ պարզել՝ խոսքը մատակարարման, ծածկույթի, թե կազմակերպման խնդրի մասին է։",
            "next_step": "Նշված տվյալներով պետք է ճշտել՝ արդյոք դեղը նախատեսված էր տրամադրման համար և որ կազմակերպությունն էր պարտավոր այն տրամադրել։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Եթե դեղը չեն տրամադրել, նախ պետք է հստակեցնել՝ որ դեղի մասին է խոսքը և որտեղ է խնդիրն առաջացել։",
    "next_step_if_missing": "Նախ նշե՛ք դեղի ամբողջական տվյալները և այն վայրը, որտեղ այն չեն տրամադրել։",
    "priority": 105
}

record_wrong = {
    "id": "complaint_missing_or_wrong_record_v1",
    "category": "complaints",
    "patterns": [
        "տվյալը սխալ է",
        "գրառումը սխալ է",
        "գրառում չկա",
        "գրառումս չկա",
        "իմ տվյալները սխալ են",
        "սխալ տեղեկատվություն է երևում",
        "missing record",
        "wrong record",
        "record is wrong"
    ],
    "approved_answer": "Այս հարցով նախ պետք է հասկանալ՝ ինչ տվյալ է բացակայում կամ սխալ երևում։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "record_issue_type",
        "record_context"
    ],
    "field_questions": {
        "record_issue_type": "Նշե՛ք՝ տվյալը բացակայում է, թե սխալ է երևում։",
        "record_context": "Նշե՛ք՝ կոնկրետ ինչ գրառման կամ տվյալների մասին է խոսքը։"
    },
    "field_values": {
        "record_issue_type": {
            "missing_record": [
                "բացակայում է",
                "չկա",
                "գրառում չկա",
                "missing"
            ],
            "wrong_record": [
                "սխալ է",
                "սխալ է երևում",
                "սխալ տվյալ",
                "wrong"
            ]
        }
    },
    "answer_rules": [
        {
            "when": {
                "record_issue_type": "missing_record",
                "record_context": "__any__"
            },
            "answer": "Եթե տվյալը բացակայում է, նախ պետք է հստակեցնել՝ որ գրառումը պետք է երևար և որ համակարգում կամ հաստատությունում է խնդիրը նկատվել։",
            "next_step": "Դրա համար պետք է ճշտել գրառման տեսակը և այն կազմակերպությունը, որտեղ տվյալը պետք է արտացոլված լիներ։"
        },
        {
            "when": {
                "record_issue_type": "wrong_record",
                "record_context": "__any__"
            },
            "answer": "Եթե տվյալը սխալ է երևում, նախ պետք է հստակեցնել՝ կոնկրետ որ մասը է սխալ և ինչ տվյալ պետք է երևար դրա փոխարեն։",
            "next_step": "Դրա համար պետք է հավաքել սխալ արտացոլված տվյալը և ճիշտ տարբերակը, ապա դիմել համապատասխան հաստատությանը հստակեցման համար։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Եթե գրառումը բացակայում է կամ սխալ է երևում, նախ պետք է հստակեցնել խնդրի տեսակը և կոնկրետ տվյալը։",
    "next_step_if_missing": "Նախ նշե՛ք՝ խոսքը բացակա գրառման, թե սխալ տվյալների մասին է։",
    "priority": 105
}

armed_visibility = {
    "id": "technical_armed_visibility_issue_v1",
    "category": "complaints",
    "patterns": [
        "արմեդում չի երևում",
        "armed-ում չի երևում",
        "չի երևում համակարգում",
        "էլեկտրոնային համակարգում չկա",
        "ArMed չի երևում",
        "ArMed-ում չկա",
        "armed visibility",
        "not visible in armed"
    ],
    "approved_answer": "Եթե տվյալը ArMed-ում չի երևում, նախ պետք է հստակեցնել՝ ինչ տվյալ պետք է երևար և որտեղ եք նկատել խնդիրը։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "armed_item_type",
        "armed_issue_context"
    ],
    "field_questions": {
        "armed_item_type": "Նշե՛ք՝ ինչ տվյալ պետք է երևար ArMed-ում։ Օրինակ՝ դեղատոմս, գրառում, ծառայություն կամ այլ տվյալ։",
        "armed_issue_context": "Նշե՛ք՝ որտեղ և երբ եք նկատել, որ տվյալը չի երևում։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "armed_item_type": "__any__",
                "armed_issue_context": "__any__"
            },
            "answer": "Եթե տվյալը ArMed-ում չի երևում, դա կարող է լինել գրառման, փոխանցման կամ տեխնիկական արտացոլման խնդիր։",
            "next_step": "Դրա համար պետք է նախ հստակեցնել, թե ինչ տվյալ պետք է երևար, ապա դիմել այն հաստատությանը կամ մասնագետին, որտեղ տվյալը ձևավորվել է։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Եթե տվյալը ArMed-ում չի երևում, նախ պետք է հստակեցնել՝ կոնկրետ ինչ տվյալ է բացակայում։",
    "next_step_if_missing": "Նախ նշե՛ք, թե ինչ տվյալ պետք է երևար ArMed-ում և որտեղ եք նկատել խնդիրը։",
    "priority": 106
}

duplicate_charge = {
    "id": "complaint_duplicate_charge_or_wrong_payment_status_v1",
    "category": "complaints",
    "patterns": [
        "կրկնակի գումար են գանձել",
        "երկու անգամ են գանձել",
        "վճարումը սխալ է երևում",
        "վճարման կարգավիճակը սխալ է",
        "կրկնակի վճարում",
        "սխալ վճարման կարգավիճակ",
        "duplicate charge",
        "wrong payment status"
    ],
    "approved_answer": "Այս դեպքում նախ պետք է հստակեցնել՝ խոսքը կրկնակի գանձման, թե սխալ վճարման կարգավիճակի մասին է։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "payment_issue_type",
        "payment_context"
    ],
    "field_questions": {
        "payment_issue_type": "Նշե՛ք՝ խոսքը կրկնակի գանձման, թե սխալ կարգավիճակի մասին է։",
        "payment_context": "Նշե՛ք՝ որ ծառայության կամ վճարման մասին է խոսքը և որտեղ եք նկատել խնդիրը։"
    },
    "field_values": {
        "payment_issue_type": {
            "duplicate_charge": [
                "կրկնակի",
                "երկու անգամ",
                "duplicate"
            ],
            "wrong_status": [
                "սխալ կարգավիճակ",
                "սխալ է երևում",
                "wrong status"
            ]
        }
    },
    "answer_rules": [
        {
            "when": {
                "payment_issue_type": "duplicate_charge",
                "payment_context": "__any__"
            },
            "answer": "Եթե գումարը երկու անգամ է գանձվել, նախ պետք է հստակեցնել՝ որ ծառայության համար է դա տեղի ունեցել և որտեղ է արտացոլվում կրկնությունը։",
            "next_step": "Դրա համար պետք է հավաքել վճարման տվյալները և դիմել համապատասխան հաստատությանը կամ ծառայության մատուցողին պարզաբանման համար։"
        },
        {
            "when": {
                "payment_issue_type": "wrong_status",
                "payment_context": "__any__"
            },
            "answer": "Եթե վճարման կարգավիճակը սխալ է երևում, նախ պետք է հստակեցնել՝ ինչ կարգավիճակ է ցուցադրվում և ինչ պետք է երևար դրա փոխարեն։",
            "next_step": "Դրա համար պետք է հավաքել վճարման կամ ծառայության տվյալները և դիմել համապատասխան հաստատությանը ճշտման համար։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Եթե վճարման տվյալները սխալ են երևում կամ կրկնակի գանձում կա, նախ պետք է հստակեցնել խնդրի տեսակը։",
    "next_step_if_missing": "Նախ նշե՛ք՝ խոսքը կրկնակի գանձման, թե սխալ վճարման կարգավիճակի մասին է։",
    "priority": 106
}

specialist_referral = {
    "id": "routing_specialist_referral_confusion_v1",
    "category": "routing",
    "patterns": [
        "նեղ մասնագետի ուղեգիր",
        "մասնագետի ուղեգիր",
        "ուղեգիր նեղ մասնագետի համար",
        "պետք է ուղեգիր մասնագետի համար",
        "մասնագետի մոտ ինչպես գնամ",
        "specialist referral",
        "referral to specialist"
    ],
    "approved_answer": "Այս հարցով նախ պետք է հստակեցնել՝ կոնկրետ որ մասնագետի մասին է խոսքը և ինչ նպատակով եք ցանկանում դիմել։",
    "allowed_answer_type": "conditional",
    "required_fields": [
        "specialist_type_or_purpose"
    ],
    "field_questions": {
        "specialist_type_or_purpose": "Նշե՛ք՝ որ մասնագետի մոտ եք ցանկանում դիմել կամ ինչ հարցով է անհրաժեշտ ուղղորդումը։"
    },
    "field_values": {},
    "answer_rules": [
        {
            "when": {
                "specialist_type_or_purpose": "__any__"
            },
            "answer": "Եթե խոսքը նեղ մասնագետի ուղղորդման մասին է, առաջին քայլը սովորաբար պոլիկլինիկա կամ բուժող բժիշկ դիմելն է։",
            "next_step": "Նշված տվյալներով պետք է ճշտել՝ տվյալ դեպքում անհրաժեշտ է ուղեգիր, թե կարելի է դիմել անմիջապես։"
        }
    ],
    "clarifiable": True,
    "partial_answer_allowed": True,
    "safe_partial_answer": "Եթե հարցը նեղ մասնագետի ուղղորդման մասին է, նախ պետք է հստակեցնել՝ որ մասնագետի կամ ինչ նպատակի մասին է խոսքը։",
    "next_step_if_missing": "Նախ նշե՛ք՝ որ մասնագետի մոտ եք ցանկանում դիմել կամ ինչ հարցով է պետք ուղղորդումը։",
    "priority": 104
}

upsert_card(KB / "complaints.json", medicine_not_provided)
upsert_card(KB / "complaints.json", record_wrong)
upsert_card(KB / "complaints.json", armed_visibility)
upsert_card(KB / "complaints.json", duplicate_charge)
upsert_card(KB / "routing.json", specialist_referral)

print("DONE")
