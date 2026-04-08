from typing import Any, Dict, Tuple


def _clean(s: str) -> str:
    return " ".join((s or "").split()).strip()


def _institution_phrase(institution: str) -> str:
    raw = _clean(institution).lower()
    mapping = {
        "պոլիկլինիկայում": "տվյալ պոլիկլինիկային",
        "հիվանդանոցում": "տվյալ հիվանդանոցին",
        "կլինիկայում": "տվյալ կլինիկային",
        "բուժհաստատությունում": "տվյալ բուժհաստատությանը",
        "դեղատանը": "տվյալ դեղատանը",
    }
    return mapping.get(raw, raw)


def _normalize_issue_target(target: str) -> str:
    raw = _clean(target).lower()
    mapping = {
        "դեղատոմսը": "դեղատոմսը",
        "դեղատոմս": "դեղատոմսը",
        "ուղեգիրը": "ուղեգիրը",
        "ուղեգիր": "ուղեգիրը",
        "գրառումը": "գրառումը",
        "գրառում": "գրառումը",
        "տվյալը": "տվյալը",
        "տվյալ": "տվյալը",
    }
    return mapping.get(raw, target)


def _compose_referral_specialist(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    need_type = collected_fields.get("need_type")
    detail = collected_fields.get("specialist_or_service")

    if need_type == "specialist" and detail:
        answer = f"Եթե ուզում եք դիմել {detail}ի, առաջին քայլը սովորաբար պոլիկլինիկա կամ ընտանեկան բժիշկն է, որովհետև հենց այնտեղ է ճշտվում՝ այս դեպքում ուղեգիր պահանջվո՞ւմ է, թե ոչ։"
        next_step = f"Դիմեք ձեր պոլիկլինիկա կամ ընտանեկան բժշկին և ճշտեք՝ {detail}ի դեպքում կարելի՞ է դիմել անմիջապես, թե պետք է ուղեգիր։"
        return _clean(answer), _clean(next_step)

    if need_type == "diagnostic" and detail:
        label = detail.upper() if detail in {"մռտ", "կտ"} else detail
        answer = f"Եթե հարցը {label}-ի մասին է, առաջին քայլը սովորաբար ձեր բժշկին կամ պոլիկլինիկային դիմելն է, որովհետև հենց այնտեղ է պարզվում՝ այդ հետազոտության համար ուղեգիր պահանջվո՞ւմ է, թե ոչ։"
        next_step = f"Դիմեք ձեր բժշկին կամ պոլիկլինիկա և ճշտեք՝ {label}-ի համար ուղեգիր պե՞տք է, և որտեղ պետք է անցնեք հետազոտությունը։"
        return _clean(answer), _clean(next_step)

    if need_type == "general":
        answer = "Եթե հարցը ընդհանուր բուժօգնության մասին է, սովորական առաջին կետը պոլիկլինիկան կամ ընտանեկան բժիշկն է։"
        next_step = "Դիմեք ձեր պոլիկլինիկա կամ ընտանեկան բժշկին՝ հետագա ուղղորդումը հասկանալու համար։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_payment_dispute(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    service_name = _clean(str(collected_fields.get("service_name_or_type", "") or ""))
    institution = _clean(str(collected_fields.get("institution_context", "") or ""))
    has_referral = bool(collected_fields.get("has_referral_context"))
    institution_target = _institution_phrase(institution)

    if service_name and institution:
        answer = f"Եթե {service_name}-ի համար {institution} ձեզնից գումար են պահանջել, դա դեռ ինքնին չի նշանակում, որ պահանջը ճիշտ էր։"
        answer += " Քանի որ նշում եք, որ ունեք ուղեգիր, կարևոր է հենց տեղում ճշտել՝ ինչ հիմքով է պահանջվել վճարը։" if has_referral else " Նախ պետք է հենց տեղում ճշտել՝ ինչ հիմքով է պահանջվել վճարը։"
        next_step = f"Դիմեք հենց {institution_target} և խնդրեք հստակ ասել՝ {service_name}-ի համար ինչ հիմքով է պահանջվում վճարը։ Եթե բացատրությունը մնում է անհասկանալի կամ հակասական, հաջորդ քայլը բողոքարկման ուղղությունն է։"
        return _clean(answer), _clean(next_step)

    if service_name:
        answer = f"Եթե {service_name}-ի համար ձեզնից գումար են պահանջել, դա դեռ ինքնին չի նշանակում, որ պահանջը ճիշտ էր։"
        answer += " Քանի որ նշում եք, որ ունեք ուղեգիր, կարևոր է հենց տեղում ճշտել՝ ինչ հիմքով է պահանջվել վճարը։" if has_referral else " Նախ պետք է ճշտել՝ ինչ հիմքով է պահանջվել վճարը։"
        next_step = f"Դիմեք այն հաստատությանը, որտեղ {service_name}-ի համար գումար են պահանջել, և խնդրեք հստակ ասել՝ ինչ հիմքով է վճարը պահանջվում։ Եթե բացատրությունը մնում է անհասկանալի կամ հակասական, հաջորդ քայլը բողոքարկման ուղղությունն է։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_record_or_visibility_issue(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    target = _normalize_issue_target(str(collected_fields.get("issue_target", "") or ""))
    system = _clean(str(collected_fields.get("issue_system", "") or ""))
    place = _clean(str(collected_fields.get("issue_place", "") or ""))
    target_subject = target

    if system == "armed" and target:
        answer = f"Եթե {target_subject} ArMed-ում չի երևում, նախ պետք է ճշտել՝ արդյոք այն ճիշտ է գրանցվել համակարգում։"
        if place == "դեղատանը":
            next_step = f"Եթե խնդիրը նկատել եք {place}, նախ ճշտեք՝ {target_subject} համակարգում ճիշտ է ձևավորվել կամ գրանցվել այն կողմից, որը պետք է այն ստեղծեր։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը թեժ գծով կամ բողոքարկման ուղղությամբ դիմելն է։"
        elif place:
            next_step = f"Նախ դիմեք այն տեղը, որտեղ {target_subject} պետք է ձևավորվեր կամ երևար, այս դեպքում՝ {place}, և խնդրեք ստուգել գրանցումը։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը թեժ գծով կամ բողոքարկման ուղղությամբ դիմելն է։"
        else:
            next_step = f"Նախ դիմեք այն տեղը, որտեղ {target_subject} պետք է ձևավորվեր կամ երևար, և խնդրեք ստուգել գրանցումը։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը թեժ գծով կամ բողոքարկման ուղղությամբ դիմելն է։"
        return _clean(answer), _clean(next_step)

    if target:
        answer = f"Եթե {target_subject} բացակայում է կամ սխալ է երևում, նախ պետք է ճշտել՝ որտեղ պետք է այն երևար կամ գրանցված լիներ։"
        next_step = "Դիմեք այն հաստատությանը կամ ծառայությանը, որտեղ այդ տվյալը պետք է գրանցվեր կամ երևար, և խնդրեք ստուգել գրանցումը։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը պաշտոնական դիմում կամ թեժ գծով կապն է։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_medicine_not_provided(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    medicine = _clean(str(collected_fields.get("medicine_name_or_type", "") or ""))
    place = _clean(str(collected_fields.get("dispense_place", "") or ""))
    has_rx = bool(collected_fields.get("has_prescription_context"))

    if medicine and place:
        answer = f"Եթե {medicine}ը {place} չեն տրամադրում, նախ պետք է ճշտել՝ խնդիրը կապված է առկայության, գրանցման, թե տրամադրման կարգի հետ։"
        if has_rx:
            answer += " Քանի որ նշում եք, որ դեղը դուրս է գրված, կարևոր է նաև ստուգել՝ արդյոք այն ճիշտ է ձևակերպվել կամ գրանցվել։"
        next_step = f"Դիմեք հենց {place} և խնդրեք հստակ ասել՝ {medicine}ը ինչու չեն տրամադրում։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը թեժ գծով կամ բողոքարկման ուղղությամբ դիմելն է։"
        return _clean(answer), _clean(next_step)

    if medicine:
        answer = f"Եթե {medicine}ը չեն տրամադրում, նախ պետք է ճշտել՝ խնդիրը կապված է առկայության, գրանցման, թե տրամադրման կարգի հետ։"
        next_step = f"Դիմեք այն տեղը, որտեղ {medicine}ը պետք է տրամադրվեր, և խնդրեք հստակ ասել՝ ինչու չեն տրամադրում այն։ Եթե խնդիրը չի լուծվում, հաջորդ քայլը թեժ գծով կամ բողոքարկման ուղղությամբ դիմելն է։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_denied_service(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    service = _clean(str(collected_fields.get("service_name_or_type", "") or ""))
    institution = _clean(str(collected_fields.get("institution_context", "") or ""))
    institution_target = _institution_phrase(institution)
    service_phrase = "ՄՌՏ-ն" if service == "ՄՌՏ" else "ԿՏ-ն" if service == "ԿՏ" else service

    if service and institution:
        answer = f"Եթե {service_phrase} {institution} մերժել են, նախ պետք է հասկանալ՝ ինչ պատճառաբանությամբ է մերժումը եղել։"
        next_step = f"Դիմեք հենց {institution_target} և խնդրեք հստակ ասել՝ {service_phrase} ինչ հիմքով են մերժել։ Եթե պատճառաբանությունը մնում է անհասկանալի կամ հակասական, հաջորդ քայլը բողոքարկման ուղղությունն է։"
        return _clean(answer), _clean(next_step)

    if service:
        answer = f"Եթե {service_phrase} մերժել են, նախ պետք է հասկանալ՝ ինչ պատճառաբանությամբ է մերժումը եղել։"
        next_step = f"Դիմեք այն հաստատությանը, որտեղ {service_phrase} մերժել են, և խնդրեք հստակ ասել մերժման պատճառը։ Եթե պատճառաբանությունը մնում է անհասկանալի կամ հակասական, հաջորդ քայլը բողոքարկման ուղղությունն է։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_eligibility_check(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    group = _clean(str(collected_fields.get("person_group", "") or ""))
    labels = {
        "elderly_65_plus": "65+ կարգավիճակը",
        "pensioner": "թոշակառու կարգավիճակը",
        "disability": "հաշմանդամության կարգավիճակը",
        "pregnancy": "հղիության կարգավիճակը",
        "child": "երեխայի կարգավիճակը",
        "social_vulnerability": "սոցիալապես անապահով կարգավիճակը",
        "worker_insured": "աշխատող կամ ապահովագրված կարգավիճակը",
    }
    label = labels.get(group, "")
    if label:
        answer = f"{label.capitalize()} կարող է նշանակություն ունենալ որոշ պետական առողջապահական ծրագրերում, բայց վերջնական իրավունքը կախված է կոնկրետ ծառայությունից կամ ծրագրից։"
        next_step = "Ճշտեք կոնկրետ որ ծառայության կամ ծրագրի մասին է խոսքը, հետո ստուգեք այդ ծառայության պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        return _clean(answer), _clean(next_step)
    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def _compose_service_coverage_check(branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    service_type = _clean(str(collected_fields.get("service_type", "") or ""))
    labels = {
        "mri": "ՄՌՏ-ի",
        "ct": "ԿՏ-ի",
        "hospitalization": "հոսպիտալացման",
        "lab": "լաբորատոր քննությունների",
        "specialist": "մասնագետի ծառայության",
        "surgery": "վիրահատության",
    }
    label = labels.get(service_type, "")

    if label:
        answer = f"{label.capitalize()} ծածկույթը կարող է կախված լինել կոնկրետ պայմաններից, ուղեգրից կամ ծրագրային հիմքից, այնպես որ վերջնական պատասխանը միայն «այո/ոչ» ձևով ճիշտ չի լինի։"
        if service_type in {"mri", "ct"}:
            next_step = "Ճշտեք՝ ունե՞ք ուղեգիր և ինչ հիմքով է ծառայությունը նշանակվել, հետո ստուգեք պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        elif service_type == "hospitalization":
            next_step = "Ճշտեք՝ խոսքը շտապ, թե պլանային հոսպիտալացման մասին է, հետո ստուգեք պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        elif service_type == "lab":
            next_step = "Ճշտեք՝ կոնկրետ որ քննության մասին է խոսքը և ինչ հիմքով է այն նշանակվել, հետո ստուգեք պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        elif service_type == "specialist":
            next_step = "Ճշտեք՝ որ մասնագետի մասին է խոսքը և ունե՞ք ուղեգիր, հետո ստուգեք պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        else:
            next_step = "Ճշտեք՝ կոնկրետ որ ծառայության մասին է խոսքը և ինչ հիմքով է այն նշանակվել, հետո ստուգեք պայմանները համապատասխան պաշտոնական աղբյուրով կամ թեժ գծով։"
        return _clean(answer), _clean(next_step)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))


def compose_answer(family: str, branch: Dict[str, Any], collected_fields: Dict[str, Any]) -> Tuple[str, str]:
    if family == "referral_specialist":
        return _compose_referral_specialist(branch, collected_fields)
    if family == "payment_dispute":
        return _compose_payment_dispute(branch, collected_fields)
    if family == "record_or_visibility_issue":
        return _compose_record_or_visibility_issue(branch, collected_fields)
    if family == "medicine_not_provided":
        return _compose_medicine_not_provided(branch, collected_fields)
    if family == "denied_service":
        return _compose_denied_service(branch, collected_fields)
    if family == "eligibility_check":
        return _compose_eligibility_check(branch, collected_fields)
    if family == "service_coverage_check":
        return _compose_service_coverage_check(branch, collected_fields)

    return _clean(branch.get("answer", "")), _clean(branch.get("next_step", ""))
