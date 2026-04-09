def normalize_text_v2(text: str) -> str:
    if text is None:
        return ""
    return " ".join(str(text).lower().strip().split())


def classify_issue_family(message: str) -> str:
    text = normalize_text_v2(message)

    payment_markers = [
        "փող են ուզում", "փող ուզեցին",
        "վճարել", "վճարում", "վճարման", "վճարած", "վճարովի",
        "գումար", "համավճար", "անվճար չի", "paid", "co pay",
        "գանձ", "կրկնակի", "երկու անգամ", "երկրորդ անգամ", "չեք վճարել",
        "պարտք է ցույց տալիս", "վճարման կարգավիճակ", "վճարումը գրանցված չէ",
    ]

    denied_service_markers = [
        "մերժել", "մերժեցին", "չեն ընդունել", "չեն արել", "չեն սպասարկել",
        "չեն տրամադրել ծառայությունը", "refused", "denied",
        "չի գրանց", "չեն գրանց", "չգրանց", "չեն կցագր",
        "հրաժարվ", "մերժում է գրանց", "տեղ չկա չեն գրանց",
    ]

    complaint_contact_markers = [
        "բողոք", "գանգատ", "թեժ գիծ", "8003", "ուր զանգեմ", "որտեղ զանգեմ",
        "որտեղ բողոքեմ", "ինչպես բողոք ներկայացնել",
    ]

    state_funding_payment_denial_markers = [
        "պետպատվեր չկա", "պետպատվերով չի անց", "ասում են պետպատվեր",
    ]

    state_funding_denied_service_markers = [
        "պետպատվեր չեն տալիս", "պետպատվեր չեն տրամադրում", "պետպատվերով չեն անում",
    ]

    eligibility_markers = [
        "իրավունք ունեմ", "իրավունք ունե՞մ", "ընդգրկվա", "ինձ հասնու",
        "կարո՞ղ եմ օգտվել", "թոշակառու", "65", "հղի", "երեխա",
        "հաշմանդամ", "սոցիալապես անապահով", "աշխատող", "ապահովագրված",
        "eligible", "eligibility", "պետպատվ", "արտոնյալ", "ինչ է հասնում",
    ]

    record_markers = [
        "չի երևում", "սխալ է երևում", "համակարգում", "արմեդ", "armed",
        "գրառում", "տվյալ", "բացակայում է", "չկա համակարգում",
    ]

    medicine_markers = [
        "դեղ", "դեղատուն", "դեղատանը", "չեն տալիս", "դուրս է գրված",
        "prescription", "medicine",
    ]

    medicine_formulary_markers = [
        "պետության ցանկ", "պետական ցանկ", "ցանկում", "ցանկի մեջ",
    ]

    medicine_strength_markers = [" մգ", " mg", " մլ", " ml"]

    medicine_dosage_form_markers = [
        "դեղապատիճ", "հաբ", "հաբեր", "օշարակ", "ներարկ", "լուծույթ", "կաթիլ",
    ]

    medicine_denial_markers = [
        "չեն տվել", "չեն տալիս", "չկա", "չունի", "չեն տրամադրել",
    ]

    coverage_markers = [
        "ծածկվո՞ւմ է", "ծածկվում է", "անվճար է", "անվճա՞ր է", "covered", "coverage",
    ]

    admission_markers = [
        "հոսպիտալ", "ստացիոնար", "պառկ", "վիրահատ", "ընդունում", "ընդունվելու",
        "պլանային", "անհետաձգելի",
    ]

    routing_markers = [
        "ուղեգիր", "մասնագետ", "specialist", "referral", "ուր դիմեմ",
        "որտեղ գնամ", "որտեղ դիմեմ", "ուր գնամ", "պոլիկլինիկա",
        "ընտանեկան բժիշկ", "սրտաբան", "նյարդաբան", "ակնաբույժ",
        "գինեկոլոգ", "ուռոլոգ", "էնդոկրինոլոգ", "օրթոպեդ", "վիրաբույժ",
        "հետազոտ", "mri", "ct",
    ]

    if any(marker in text for marker in payment_markers):
        return "payment_dispute"

    if any(marker in text for marker in denied_service_markers):
        return "denied_service"

    if any(marker in text for marker in complaint_contact_markers):
        return "complaint_contact_help"

    if any(marker in text for marker in state_funding_payment_denial_markers):
        return "payment_dispute"

    if any(marker in text for marker in state_funding_denied_service_markers):
        return "denied_service"

    if any(marker in text for marker in eligibility_markers):
        return "eligibility_check"

    if any(marker in text for marker in record_markers):
        return "record_or_visibility_issue"

    if any(marker in text for marker in admission_markers):
        return "service_coverage_check"

    if any(marker in text for marker in coverage_markers) and any(marker in text for marker in ("mri", "մռտ", "ct", "կտ", "անալիզ", "վերլուծություն", "մասնագետ")):
        return "referral_specialist"

    # Coverage should win over referral when explicit coverage wording is present.
    if any(marker in text for marker in coverage_markers):
        return "service_coverage_check"

    if any(marker in text for marker in medicine_formulary_markers) and ("կա" in text or any(marker in text for marker in medicine_markers)):
        return "service_coverage_check"

    if (
        any(marker in text for marker in medicine_strength_markers)
        and any(marker in text for marker in medicine_dosage_form_markers)
        and not any(marker in text for marker in medicine_denial_markers)
    ):
        return "service_coverage_check"

    if any(marker in text for marker in medicine_markers):
        return "medicine_not_provided"

    if any(marker in text for marker in routing_markers):
        return "referral_specialist"

    return "unknown"
