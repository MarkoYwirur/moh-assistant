import json
from pathlib import Path

KB = Path(r"C:\Users\Asus\Desktop\moh-assistant\kb\routing.json")

data = json.loads(KB.read_text(encoding="utf-8-sig"))
cards = data if isinstance(data, list) else data["cards"]

for card in cards:
    if card.get("id") == "routing_specialist_referral_confusion_v1":
        card["safe_partial_answer"] = "Եթե խոսքը նեղ մասնագետի դիմելու մասին է, առաջին կարևոր հարցը տվյալ մասնագետի կամ նպատակի հստակեցումն է։"
        card["answer_rules"] = [
            {
                "when": {
                    "specialist_type_or_purpose": "__any__"
                },
                "answer": "Եթե ցանկանում եք դիմել նեղ մասնագետի, առաջին քայլը սովորաբար ճիշտ ուղղորդման աղբյուրը պարզելն է՝ հատկապես երբ հարցը վերաբերում է կազմակերպված բուժօգնությանը կամ ուղեգրով ծառայությանը։",
                "next_step": "Նախ դիմեք ձեր պոլիկլինիկային կամ բուժող բժշկին՝ հստակեցնելու համար, թե տվյալ մասնագետի դեպքում ուղեգիր պահանջվո՞ւմ է, թե կարելի է դիմել անմիջապես։"
            }
        ]

payload = cards if isinstance(data, list) else {"cards": cards}
KB.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("SPECIALIST_ROUTING_UPGRADED")
