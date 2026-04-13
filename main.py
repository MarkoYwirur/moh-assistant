from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from decision_engine import decide
from generator import build_response
from logging_utils import append_request_log
from router import (
    _match_field_values_from_card,
    coerce_field_value,
    get_card_by_id,
    get_top_candidates,
    load_all_cards,
    normalize_text,
    should_continue_pending_flow,
)
from validator import validate_response
from app.controller_v2 import run_controller_v2


app = FastAPI(title="MOH Assistant Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    state: dict[str, Any] | None = None


COMPLAINT_PROCEDURE_SIGNALS = (
    "ինչ տվյալներ",
    "ինչպես է քննվում",
    "բողոքը ինչպես է քննվում",
    "ինչ է լինում հետո",
    "բողոքից հետո",
    "բողոք ներկայացնելուց հետո",
    "ինչ քայլերով",
    "ինչպես բողոք ներկայացնել",
    "ինչ ժամկետում պետք է բողոք ներկայացնել",
    "մեկ տարվա ընթացքում բողոք",
)

COMPLAINT_SERVICE_PROCEDURE_SIGNALS = (
    "ծառայություն",
    "կազմակերպում",
    "հիվանդանոց",
    "վարչական",
    "inspection",
    "տեսչական",
)

COMPLAINT_CONTACT_SIGNALS = (
    "որտեղ դիմել",
    "հեռախոս",
    "8003",
    "կապ",
    "թեժ գիծ",
    "զանգահարել",
)

COMPLAINT_ETHICS_SIGNALS = (
    "բժշկի վարքագիծ",
    "բուժաշխատողի վարքագիծ",
    "էթիկա",
    "խախտում",
    "էթիկայի հանձնաժողով",
)

COMPLAINT_DISPUTE_SIGNALS = (
    "փող",
    "փող են ուզում",
    "փող ուզեցին",
    "գումար են ուզում",
    "գումար են պահանջում",
    "վճարել եմ",
    "պետք է անվճար լիներ",
    "գումար",
    "վճարովի",
)

COMPLAINT_DUPLICATE_STATUS_SIGNALS = (
    "կրկնակի",
    "երկու անգամ",
    "երկրորդ անգամ",
    "նորից",
    "կրկին",
    "կարգավիճակ",
    "վճարումը սխալ է երևում",
    "վճարման կարգավիճակը սխալ է",
    "պարտք է ցույց տալիս",
    "գրանցված չէ",
    "չեք վճարել",
    "վճարել եմ բայց",
)

MIXED_ENTITLEMENT_SIGNALS = (
    "անվճար",
    "ծածկվում",
    "ծածկվում է",
    "պետպատվ",
    "պետպատվեր",
    "պետպատվերով",
    "պետական ծրագիր",
    "արտոնյալ",
)

MIXED_REFERRAL_SIGNALS = (
    "ուղեգ",
    "ուղեգիր",
    "ուղղորդ",
    "ուղղորդում",
    "թուղթ",
    "ընտանեկան բժիշկ",
    "պոլիկլինիկա",
    "որտեղից",
)

MIXED_CONCRETE_SERVICE_ANCHORS = (
    "մռտ",
    "mri",
    "կտ",
    "ct",
    "լաբորատոր",
    "անալիզ",
    "սրտաբան",
    "նյարդաբան",
    "ակնաբույժ",
    "մասնագետ",
)

AMBIGUOUS_PAYMENT_VISIBILITY_PHRASES = {
    "վճարումը չի երևում",
    "վճարումը չկա",
    "վճարումը չի ցուցադրվում",
}

GENERIC_COMPLAINT_INTENT_PHRASES = {
    normalize_text("որտեղ բողոքեմ"),
    normalize_text("ինչպես դիմեմ բողոքով"),
    normalize_text("բողոք ունեմ ուր դիմեմ"),
    normalize_text("ինչպես բողոք ներկայացնել"),
    normalize_text("բողոքի ընթացակարգը որն է"),
    normalize_text("բողոքից հետո ինչ է լինում"),
    normalize_text("բողոքը ինչպես է քննվում"),
}

EXPLICIT_COMPLAINT_CONTACT_PHRASES = {
    normalize_text("ուր զանգեմ բողոքի համար"),
    normalize_text("որտեղ զանգեմ բողոքի համար"),
    normalize_text("թեժ գիծ կա բողոքի համար"),
    normalize_text("8003-ով կարո՞ղ եմ բողոքել"),
}

COMPLAINT_HARM_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_HARM_PROVIDER_ANCHORS = (
    "բուժաշխատող",
    "բժիշկ",
    "բժշկ",
)

COMPLAINT_HARM_FAULT_ANCHORS = (
    "մեղքով",
    "վնաս",
)

COMPLAINT_HARM_CONTACT_DISQUALIFIERS = (
    "պետպատվ",
    "վճար",
    "անվճար",
    "արտոնյալ",
    "հիվանդանոց ընդուն",
    "հոսպիտալ",
    "վիրահատ",
)

COMPLAINT_MISCONDUCT_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_MISCONDUCT_PROVIDER_ANCHORS = (
    "բուժաշխատող",
    "մեդաշխատող",
    "բժիշկ",
    "բժշկ",
)

COMPLAINT_MISCONDUCT_BEHAVIOR_ANCHORS = (
    "կոպիտ",
    "վիրավոր",
    "վատ է վարվել",
    "վատ վարվել",
    "վարք",
    "էթիկ",
    "ոչ պատշաճ",
)

COMPLAINT_MISCONDUCT_CONTACT_DISQUALIFIERS = (
    "պետպատվ",
    "վճար",
    "անվճար",
    "արտոնյալ",
    "հիվանդանոց ընդուն",
    "հոսպիտալ",
    "վիրահատ",
    "մեղքով",
    "վնաս",
)

COMPLAINT_DENIED_SERVICE_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_DENIED_SERVICE_REFUSAL_ANCHORS = (
    "մերժել",
    "մերժված",
    "չեն սպասարկել",
    "չեն ընդունել",
    "չեն տվել",
    "հրաժարվել",
    "չեն գրանց",
)

COMPLAINT_DENIED_SERVICE_CONTACT_DISQUALIFIERS = (
    "պետպատվ",
    "վճար",
    "վճարովի",
    "համավճար",
    "փող",
    "կոպիտ",
    "վիրավոր",
    "վարք",
    "էթիկ",
    "մեղքով",
    "վնաս",
    "հիվանդանոց ընդուն",
    "հոսպիտալ",
    "վիրահատ",
)

COMPLAINT_DUPLICATE_STATUS_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_DUPLICATE_STATUS_MARKERS = (
    "երկու անգամ",
    "կրկնակի",
    "նորից",
    "պարտք է ցույց տալիս",
    "գրանցված չէ վճարումը",
    "վճարումը գրանցված չէ",
    "վճարումը չի երևում",
    "վճարման տվյալներն են սխալ երևում",
    "վճարումը սխալ է երևում",
)

COMPLAINT_DUPLICATE_STATUS_CONTACT_DISQUALIFIERS = (
    "արմեդ",
    "armed",
    "պետպատվ",
    "վճարովի",
    "համավճար",
    "գումար են պահանջել",
    "գումար են ուզում",
    "փող են ուզում",
    "գրառում",
    "բուժման տվյալ",
    "բուժման պատմ",
    "հիվանդանոց ընդուն",
    "հոսպիտալ",
    "վիրահատ",
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
)

COMPLAINT_ARMED_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_ARMED_VISIBILITY_MARKERS = (
    "արմեդ",
    "armed",
)

COMPLAINT_ARMED_RECORD_MARKERS = (
    "չի երևում",
    "բացակայում",
    "սխալ է երևում",
    "սխալ տվյալ",
    "տվյալ",
    "գրառում",
    "ուղեգիր",
    "պատասխան",
)

COMPLAINT_ARMED_CONTACT_DISQUALIFIERS = (
    "վճար",
    "պարտք",
    "կրկնակի",
    "երկու անգամ",
    "գումար",
    "պետպատվ",
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
    "մերժել",
    "հրաժարվել",
    "չեն գրանց",
)

COMPLAINT_RECORD_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_RECORD_CONTACT_MARKERS = (
    "տվյալ",
    "գրառում",
    "բուժման տվյալ",
    "բուժման պատմ",
    "բացակայում",
    "չի երևում",
    "սխալ է երևում",
    "սխալ տվյալ",
    "պատասխան",
)

COMPLAINT_RECORD_CONTACT_DISQUALIFIERS = (
    "արմեդ",
    "armed",
    "վճար",
    "պարտք",
    "կրկնակի",
    "երկու անգամ",
    "պետպատվ",
    "գումար",
    "համավճար",
    "ուղեգիր",
    "ուղեգ",
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
    "մերժել",
    "հրաժարվել",
    "չեն գրանց",
    "հիվանդանոց ընդուն",
    "հոսպիտալ",
    "վիրահատ",
)

COMPLAINT_INSPECTION_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_INSPECTION_SCOPE_MARKERS = (
    "հիվանդանոց",
    "ծառայություն",
    "կազմակերպ",
    "վարչական",
    "հերթ",
    "դժգոհ",
)

COMPLAINT_INSPECTION_CONTACT_DISQUALIFIERS = (
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "էթիկ",
    "մեղքով",
    "վնաս",
    "մերժել",
    "հրաժարվել",
    "չեն գրանց",
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "արմեդ",
    "armed",
    "տվյալ",
    "գրառում",
    "ուղեգիր",
    "ուղեգ",
)

COMPLAINT_MEDICINE_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_MEDICINE_SCOPE_MARKERS = (
    "դեղ",
    "դեղատ",
    "դեղատոմս",
    "տրամադրել",
)

COMPLAINT_MEDICINE_REFUSAL_MARKERS = (
    "չեն տվել",
    "չեն տալիս",
    "չեն տրամադրել",
    "չի տալիս",
    "չի տրամադրել",
)

COMPLAINT_MEDICINE_CONTACT_DISQUALIFIERS = (
    "արմեդ",
    "armed",
    "ծածկ",
    "անվճար",
    "արտոնյալ",
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "գումար",
    "ուղեգիր չեն տալիս",
    "ուղեգ չեն տալիս",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
    "հիվանդանոց",
    "կազմակերպ",
    "վարչական",
)

COMPLAINT_REFERRAL_DENIAL_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_REFERRAL_DENIAL_SCOPE_MARKERS = (
    "ուղեգիր",
    "ուղեգ",
    "ուղղորդ",
)

COMPLAINT_REFERRAL_DENIAL_REFUSAL_MARKERS = (
    "չեն տալիս",
    "չեն տվել",
    "մերժել",
    "մերժված",
    "չեն անում",
    "հրաժարվել",
)

COMPLAINT_REFERRAL_DENIAL_CONTACT_DISQUALIFIERS = (
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "արմեդ",
    "armed",
    "դեղ",
    "կոպիտ",
    "վիրավոր",
    "բուժաշխատողի վարք",
    "մեղքով",
    "վնաս",
    "հիվանդանոց",
    "կազմակերպ",
    "վարչական",
)

COMPLAINT_WAITING_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_WAITING_SCOPE_MARKERS = (
    "հերթ",
    "սպաս",
    "սպասման ժամ",
    "սպասեց",
    "երկար սպաս",
)

COMPLAINT_WAITING_CONTACT_DISQUALIFIERS = (
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "արմեդ",
    "armed",
    "դեղ",
    "ուղեգիր",
    "ուղեգ",
    "մերժել",
    "հրաժարվել",
    "չեն գրանց",
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
)

COMPLAINT_PHARMACY_SERVICE_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_PHARMACY_SERVICE_SCOPE_MARKERS = (
    "դեղատ",
    "սպասարկ",
    "վարչական",
    "դժգոհ",
)

COMPLAINT_PHARMACY_SERVICE_CONTACT_DISQUALIFIERS = (
    "դեղը չեն տվել",
    "չեն տրամադրել",
    "չեն տալիս",
    "չի ծածկ",
    "ծածկ",
    "անվճար",
    "արտոնյալ",
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "արմեդ",
    "armed",
    "դեղատոմս",
    "կոպիտ",
    "վիրավոր",
    "բուժաշխատողի վարք",
    "մեղքով",
    "վնաս",
    "հերթ",
    "սպասման ժամ",
    "երկար սպաս",
    "ուղեգիր",
    "ուղեգ",
)

COMPLAINT_INVESTIGATION_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "բողոքով",
    "բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "ինչպես բողոք",
)

COMPLAINT_INVESTIGATION_SCOPE_MARKERS = (
    "անալիզ",
    "հետազոտ",
    "լաբորատոր",
    "մռտ",
    "mri",
    "կտ",
    "ct",
)

COMPLAINT_INVESTIGATION_REFUSAL_MARKERS = (
    "չեն արել",
    "չեն կատարել",
    "չեն ընդունել",
    "մերժել",
    "մերժված",
    "չեն անում",
    "չի արել",
)

COMPLAINT_INVESTIGATION_CONTACT_DISQUALIFIERS = (
    "ուղեգիր չեն տալիս",
    "ուղեգ չեն տալիս",
    "դեղ",
    "պետպատվ",
    "վճար",
    "փող",
    "համավճար",
    "արմեդ",
    "armed",
    "բուժաշխատողի վարք",
    "կոպիտ",
    "վիրավոր",
    "մեղքով",
    "վնաս",
    "հերթ",
    "սպասման ժամ",
    "երկար սպաս",
)

ADMISSION_PROCESS_ANCHORS = (
    "հիվանդանոց ընդուն",
    "ընդունում հիվանդանոց",
    "հիվանդանոց պառկ",
    "հոսպիտալաց",
    "ստացիոնար",
    "ստացիոնար ընդուն",
    "պառկեմ հիվանդանոց",
    "վիրահատ",
)

ADMISSION_PROCESS_QUESTION_ANCHORS = (
    "կարգ",
    "ինչպես",
    "ոնց",
    "ինչ անեմ",
)

ADMISSION_REQUIREMENTS_QUESTION_ANCHORS = (
    "ինչ է պետք",
    "ինչ պետք է",
    "ինչ փաստաթուղթ",
    "ինչ թուղթ",
    "ինչ documents",
)

ADMISSION_POLICY_QUESTION_ANCHORS = (
    "ինչ պայմաններով",
    "ինչ դեպքերում",
)

ADMISSION_PROCESS_ROUTING_DISQUALIFIERS = (
    "ուղեգ",
    "ուր դիմեմ",
    "ում դիմեմ",
    "որտեղ դիմեմ",
    "պոլիկլինիկ",
    "ընտանեկան բժիշկ",
)

ADMISSION_PROCESS_COVERAGE_DISQUALIFIERS = (
    "անվճա",
    "ծածկ",
    "պետպատվ",
    "իրավունք",
    "արտոնյալ",
)

ADMISSION_PROCESS_DISPUTE_DISQUALIFIERS = (
    "վճար",
    "գումար",
    "փող",
)

ADMISSION_PROCESS_MEDICAL_RISK_DISQUALIFIERS = (
    "ցավ",
    "արյուն",
    "ինչ դեղ",
    "ինչ խմեմ",
    "ախտանիշ",
    "103",
    "ջերմ",
    "շնչ",
    "շտապ օգնություն",
    "օգնեք ինձ",
)

POLYCLINIC_TRANSFER_OWNER_ID = "faq_39_ինչպե_ս_քաղաքացիները_կարող_են_գրանցվել_ընտանեկան_բժշկի_մոտ"

POLYCLINIC_TRANSFER_INSTITUTION_ANCHORS = (
    "պոլիկլինիկ",
    "ընտանեկան բժիշկ",
    "ընտանեկան բժշկ",
    "կցագր",
)

POLYCLINIC_TRANSFER_CHANGE_ANCHORS = (
    "փոխ",
    "տեղափոխ",
    "ուրիշ",
    "այլ",
    "գրանցվ",
    "կցագրվ",
)

POLYCLINIC_TRANSFER_DISQUALIFIERS = (
    "չեն ուզում",
    "չեն անում",
    "չեմ երև",
    "չի երև",
    "համակարգում",
    "բողոք",
    "մերժ",
    "չեն գրանց",
)

FAMILY_DOCTOR_TRANSFER_REFUSAL_CONTACT_INTENT_ANCHORS = (
    "բողոք",
    "որտեղ բողոքեմ",
    "բողոք ներկայաց",
    "ուր դիմեմ",
)

FAMILY_DOCTOR_TRANSFER_SCOPE_ANCHORS = (
    "պոլիկլինիկ",
    "ընտանեկան բժիշկ",
    "ընտանեկան բժշկ",
    "գրանց",
    "կցագր",
)

FAMILY_DOCTOR_TRANSFER_CHANGE_ANCHORS = (
    "փոխ",
    "տեղափոխ",
    "ուրիշ",
    "այլ",
)

FAMILY_DOCTOR_TRANSFER_REFUSAL_ANCHORS = (
    "չեմ կարող",
    "չեն գրանց",
    "չի գրանց",
    "մերժ",
    "հրաժարվ",
)

FAMILY_DOCTOR_TRANSFER_REFUSAL_CONTACT_DISQUALIFIERS = (
    "երբ",
    "ինչ հիմք",
    "ինչ պատճառ",
    "կարող է",
    "որտեղ գնամ",
)

FAMILY_DOCTOR_REFUSAL_RULE_OWNER_ID = "faq_40_երբ_կարող_է_ընտանեկան_բժիշկը_հրաժարվել_գրանցելուց"

FAMILY_DOCTOR_REGISTRATION_ANCHORS = (
    "ընտանեկան բժիշկ",
    "ընտանեկան բժշկ",
    "պոլիկլինիկ",
    "գրանց",
    "կցագր",
)

FAMILY_DOCTOR_REFUSAL_ANCHORS = (
    "չի գրանց",
    "չեն գրանց",
    "չգրանց",
    "չեմ կարող գրանցվ",
    "չեմ կարող կցագրվ",
    "չեն կցագր",
    "չեն անում",
    "հրաժարվ",
    "մերժ",
    "տեղ չկա",
)

FAMILY_DOCTOR_REFUSAL_RULE_QUESTION_ANCHORS = (
    "երբ",
    "ինչ հիմք",
    "ինչ պատճառ",
    "ինչու",
    "կարող է",
)

FAMILY_DOCTOR_REGISTRATION_TRANSFER_DISQUALIFIERS = (
    "փոխ",
    "տեղափոխ",
    "ուրիշ",
    "այլ",
)

REFERRAL_STATUS_SERVICE_ANCHORS = (
    "մռտ",
    "mri",
    "մագնիսառեզոնանսային",
    "կտ",
    "ct",
    "համակարգչային տոմոգրաֆիա",
    "կոմպյուտերային տոմոգրաֆիա",
    "անալիզ",
    "վերլուծություն",
    "լաբորատոր",
    "մասնագետ",
)

REFERRAL_STATUS_PROCESS_ANCHORS = (
    "ուղեգ",
    "նշանակ",
    "անվճա",
    "ծածկ",
    "առանց ուղեգրի",
    "պե տք",
)

SPECIALIST_REFERRAL_STATUS_ANCHORS = (
    "սրտաբան",
    "նյարդաբան",
    "ակնաբույժ",
    "մաշկաբան",
    "գինեկոլոգ",
    "էնդոկրինոլոգ",
)

SPECIALIST_REFERRAL_PROCESS_ANCHORS = (
    "ուղեգ",
    "առանց ուղեգրի",
    "չունեմ",
    "չկա",
    "պետք է",
    "պիտի",
    "նշանակ",
    "ինչ է պետք",
    "նախ",
)

SPECIALIST_REFERRAL_STATUS_DISQUALIFIERS = (
    "ուր դիմեմ",
    "որտեղ գնամ",
    "որտեղ դիմեմ",
    "որտեղից",
    "բողոք",
    "անվճար",
    "ծածկ",
    "պետպատվ",
    "հիվանդանոց",
    "ընդունում",
)

MRI_CT_REQUIREMENTS_ANCHORS = (
    "մռտ",
    "mri",
    "մագնիսառեզոնանսային",
    "կտ",
    "ct",
    "համակարգչային տոմոգրաֆիա",
    "կոմպյուտերային տոմոգրաֆիա",
)

MRI_CT_REQUIREMENTS_QUERY_ANCHORS = (
    "ինչ է պետք",
    "ինչ պետք է ունենամ",
    "ինչ փաստաթուղթ",
    "ինչ պետք է ներկայացնեմ",
    "ինչ պետք է տանեմ",
    "ինչ է անհրաժեշտ",
    "ինչ պիտի ունենամ",
    "ինչ է հարկավոր",
    "հերթագրվ",
)

MRI_CT_ROUTING_QUERY_ANCHORS = (
    "ինչպես գրանցվեմ",
    "ինչպես հերթագրվեմ",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "որտեղ գնամ",
)

MRI_CT_ROUTING_DISQUALIFIERS = (
    "ուղեգ",
    "պետք է",
    "ինչ է պետք",
    "ինչ փաստաթուղթ",
    "անվճա",
    "ծածկ",
    "պետպատվ",
    "բողոք",
)

MRI_CT_REQUIREMENTS_DISQUALIFIERS = (
    "ուր դիմեմ",
    "որտեղ գնամ",
    "որտեղ դիմեմ",
    "որտեղից",
    "ինչ անեմ",
    "անվճար",
    "ծածկ",
    "պետպատվ",
    "բողոք",
    "հիվանդանոց",
    "վիրահատ",
    "ընդունում",
)

STRUCTURED_DIRECT_POLICY_KEYS = ("what_this_is", "what_matters", "where_to_go")
STRUCTURED_DIRECT_NEXT_KEYS = ("first_next_step", "escalation_route", "constraints", "special_case")

MEDICINE_STATE_LIST_OWNER_ID = "medicine_coverage_exact_name_dosage_form_v2"

MEDICINE_STATE_LIST_ANCHORS = (
    "պետության ցանկ",
    "պետական ցանկ",
)

MEDICINE_STATE_LIST_QUERY_ANCHORS = (
    "կա",
    "մտն",
    "ներառ",
    "ցանկում",
)

MEDICINE_STATE_LIST_DISQUALIFIERS = (
    "չեն տվել",
    "չեն տալիս",
    "չկա",
    "չեն տրամադրել",
    "չեմ ստացել",
)

MEDICINE_STATE_LIST_ELIGIBILITY_DISQUALIFIERS = (
    "ովքեր",
    "ով իրավունք",
    "ինչ է հասնում",
    "պետպատվ",
    "արտոնյալ",
    "հղի",
    "երեխա",
    "հաշմանդամ",
    "թոշակառու",
)

PHARMACY_OVERSIGHT_OWNER_ID = "faq_31_ո_վ_վերահսկում_է_դեղերի_որակը_տրամադրումը_դեղատներում"

PHARMACY_OVERSIGHT_ANCHORS = (
    "դեղատ",
    "դեղերի որակ",
    "որակը",
    "տրամադրում",
    "վերահսկ",
)

PHARMACY_OVERSIGHT_DISQUALIFIERS = (
    "չեն տվել",
    "չեն տալիս",
    "չկա",
    "չի անցնում",
    "պետպատվ",
    "վճար",
    "անվճար",
    "արտոնյալ",
    "հիվանդանոց",
    "վիրահատ",
    "գաղտնի",
    "տվյալ",
)

CONFIDENTIALITY_OWNER_ID = "faq_47_ինչպե_ս_է_ապահովվում_բժշկական_գաղտնիությունը_անձնական_տվյալների_պաշտպանությունը"

FOREIGN_CITIZEN_LEGAL_BASIS_OWNER_ID = "faq_26_ի_նչ_իրավական_ակտերով_է_իրականացվում_օտարերկրյա_քաղաքացիների_բժշկական_օգնություն"
PROVIDER_LIABILITY_OWNER_ID = "faq_27_ի_նչ_պատասխանատվություն_են_կրում_բժշկական_օգնություն_իրականացնողները_իրենց_մեղքո"

CONFIDENTIALITY_CORE_ANCHORS = (
    "բժշկական գաղտնի",
    "անձնական տվյալ",
    "բժշկական տվյալ",
    "տվյալների պաշտպան",
)

CONFIDENTIALITY_QUERY_ANCHORS = (
    "տես",
    "ով կարող",
    "ով է կարող",
    "պաշտպան",
    "պահպան",
    "գաղտնի",
)

CONFIDENTIALITY_DISQUALIFIERS = (
    "չի երև",
    "սխալ",
    "բացակա",
    "համակարգում",
    "պետպատվ",
    "անվճար",
    "արտոնյալ",
    "իրավական հիմ",
    "իրավունք",
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "վճար",
    "չեն տվել",
    "դեղատ",
    "հիվանդանոց",
    "վիրահատ",
    "ընդունում",
)

FOREIGN_CITIZEN_ANCHORS = (
    "օտարերկր",
    "օտարերկրյա քաղաք",
)

FOREIGN_CITIZEN_LEGAL_ANCHORS = (
    "իրավական",
    "օրենք",
    "օրենսդր",
    "ակտ",
    "կարգավորվ",
    "հիմ",
)

FOREIGN_CITIZEN_HEALTHCARE_ANCHORS = (
    "բուժօգն",
    "բժշկական օգն",
    "սպասարկ",
)

FOREIGN_CITIZEN_LEGAL_DISQUALIFIERS = (
    "անվճար",
    "արտոնյալ",
    "պետպատվ",
    "վճար",
    "չի անցնում",
    "իրավունք",
    "հիվանդանոց",
    "ընդունում",
    "հոսպիտալ",
    "վիրահատ",
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "գաղտնի",
    "տվյալ",
)

PROVIDER_LIABILITY_CORE_ANCHORS = (
    "պատասխանատվ",
    "մեղքով",
    "վնաս",
)

PROVIDER_LIABILITY_PROVIDER_ANCHORS = (
    "բուժաշխատող",
    "բժիշկ",
    "բժշկ",
    "բժշկական օգնություն իրականացնող",
)

PROVIDER_LIABILITY_DISQUALIFIERS = (
    "բողոք",
    "ուր զանգեմ",
    "որտեղ բողոքեմ",
    "բողոք ներկայաց",
    "պետպատվ",
    "անվճար",
    "արտոնյալ",
    "իրավունք",
    "իրավական հիմ",
    "հիվանդանոց",
    "ընդունում",
    "հոսպիտալ",
    "վիրահատ",
    "վճար",
    "ինչ անեմ",
    "օգնեք",
    "ցավ",
    "արյուն",
    "ախտանիշ",
    "դեղ",
)

EXPLICIT_ELIGIBILITY_QUERY_ANCHORS = (
    "ովքեր կարող են օգտվել",
    "ով կարող է օգտվել",
    "ով իրավունք ունի",
    "ինչ իրավունք ունի",
    "շահառու",
    "պետպատվերից",
    "պետպատվեր ունի",
    "անվճար բուժօգն",
    "արտոնյալ բուժօգն",
)

EXPLICIT_ELIGIBILITY_DISQUALIFIERS = (
    "իրավական",
    "օրենք",
    "օրենսդր",
    "ակտ",
    "դեղ",
    "դեղատ",
    "ուղեգ",
    "մռտ",
    "կտ",
    "հետազոտ",
    "անալիզ",
    "մասնագետ",
    "հիվանդանոց",
    "վիրահատ",
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
)

GENERAL_MEDICINE_COVERAGE_ANCHORS = (
    "դեղ",
    "հաբ",
    "դեղահատ",
    "պարկուճ",
    "օշարակ",
    "ներարկ",
    "ինսուլին",
)

GENERAL_MEDICINE_COVERAGE_QUERY_ANCHORS = (
    "ծածկ",
    "անվճա",
    "պետպատվերով",
    "ցանկ",
    "ծածկույթ",
)

GENERAL_MEDICINE_COVERAGE_DISQUALIFIERS = (
    "չեն տվել",
    "չեն տալիս",
    "չեն տրամադրել",
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "վճար",
    "գումար",
    "երկու անգամ",
    "կրկնակի",
    "հիվանդանոց",
    "վիրահատ",
    "արմեդ",
    "armed",
)

ARMED_VISIBILITY_ISSUE_MARKERS = (
    "չի երևում",
    "բացակայում",
    "ցույց չի տալիս",
    "չի ցույց տալիս",
    "սխալ է երևում",
)

ARMED_VISIBILITY_TARGET_MARKERS = (
    "գրառում",
    "տվյալ",
    "դեղատոմս",
    "ծառայություն",
    "ցույց",
)

ARMED_VISIBILITY_ISSUE_DISQUALIFIERS = (
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "վճար",
    "գումար",
    "երկու անգամ",
    "կրկնակի",
)

RECORD_ISSUE_MARKERS = (
    "գրառում",
    "բուժման պատմ",
    "էլեկտրոնային գրառում",
    "բժշկական գրառում",
    "տվյալ",
)

RECORD_ISSUE_QUERY_MARKERS = (
    "բացակայում",
    "չի երևում",
    "սխալ է",
    "սխալ են",
    "սխալ տվյալ",
)

RECORD_ISSUE_DISQUALIFIERS = (
    "արմեդ",
    "armed",
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "վճար",
    "գումար",
    "երկու անգամ",
    "կրկնակի",
    "հիվանդանոց",
    "վիրահատ",
)

DUPLICATE_STATUS_ISSUE_MARKERS = (
    "վճարման կարգավիճակ",
    "կարգավիճակը սխալ",
    "վճար եմ արել",
    "վճարել եմ բայց",
    "չի նստել",
)

DUPLICATE_STATUS_ISSUE_DISQUALIFIERS = (
    "բողոք",
    "ուր դիմեմ",
    "որտեղ դիմեմ",
    "արմեդ",
    "armed",
    "գրառում",
    "տվյալ",
    "պետպատվ",
    "արտոնյալ",
    "հղի",
    "երեխա",
    "թոշակառու",
    "հաշմանդամ",
)


def _is_service_procedure_complaint(normalized: str) -> bool:
    has_complaint_anchor = any(term in normalized for term in ("բողոք", "բողոք ներկայացնել", "գանգատ"))
    if not has_complaint_anchor:
        return False

    has_contact_signal = any(term in normalized for term in COMPLAINT_CONTACT_SIGNALS)
    has_ethics_signal = any(term in normalized for term in COMPLAINT_ETHICS_SIGNALS)
    has_child_signal = "երեխա" in normalized
    has_service_signal = any(term in normalized for term in COMPLAINT_SERVICE_PROCEDURE_SIGNALS)

    return has_service_signal and not (has_contact_signal or has_ethics_signal or has_child_signal)


def _infer_complaint_subtype(user_text: str) -> str | None:
    normalized = normalize_text(user_text)
    if not normalized:
        return None

    has_complaint_anchor = any(term in normalized for term in ("բողոք", "գանգատ"))
    is_child_medical_aid_contact = (
        "բողոք" in normalized
        and any(term in normalized for term in ("երեխայի բժշկական օգնություն", "երեխաների բժշկական օգնություն", "սպասարկման մասին"))
    )

    if any(term in normalized for term in COMPLAINT_CONTACT_SIGNALS):
        return "contact"

    if is_child_medical_aid_contact:
        return "contact"

    if any(term in normalized for term in COMPLAINT_DUPLICATE_STATUS_SIGNALS):
        return "duplicate_status"

    if any(term in normalized for term in COMPLAINT_DISPUTE_SIGNALS):
        return "dispute"

    if any(term in normalized for term in COMPLAINT_ETHICS_SIGNALS):
        return "ethics"

    if _is_service_procedure_complaint(normalized):
        return "service_procedure"

    if has_complaint_anchor and any(term in normalized for term in COMPLAINT_PROCEDURE_SIGNALS):
        return "procedure"

    return None


def _apply_complaint_subtype_bias(candidates: list[dict[str, Any]], complaint_subtype: str | None) -> list[dict[str, Any]]:
    if not candidates or complaint_subtype is None:
        return candidates

    subtype_targets = {
        "procedure": ("complaint_40_provider_misconduct", 5.0),
        "service_procedure": ("complaint_29_inspection", 4.0),
        "ethics": ("complaint_40_provider_misconduct", 5.0),
        "contact": ("complaint_2_official_complaint_channels", 4.0),
        "dispute": ("complaint_unexpected_payment_dispute_v2", 4.0),
        "duplicate_status": ("complaint_duplicate_charge_or_wrong_payment_status_v1", 4.0),
    }
    target = subtype_targets.get(complaint_subtype)
    if target is None:
        return candidates

    target_id, boost = target
    adjusted = []
    changed = False
    for candidate in candidates:
        updated = dict(candidate)
        if candidate["card"].get("id") == target_id:
            updated["score"] = round(candidate["score"] + boost, 4)
            changed = True
        adjusted.append(updated)

    if not changed:
        return candidates

    adjusted.sort(key=lambda item: item["score"], reverse=True)
    return adjusted


def _infer_service_access_subtype(user_text: str) -> str | None:
    normalized = normalize_text(user_text)
    if not normalized:
        return None

    has_service_anchor = any(term in normalized for term in REFERRAL_STATUS_SERVICE_ANCHORS)
    has_process_anchor = any(term in normalized for term in REFERRAL_STATUS_PROCESS_ANCHORS)

    if has_service_anchor and has_process_anchor:
        return "referral_status"

    return None


def _apply_service_access_bias(candidates: list[dict[str, Any]], service_access_subtype: str | None) -> list[dict[str, Any]]:
    if not candidates or service_access_subtype is None:
        return candidates

    subtype_targets = {
        "referral_status": ("service_referral_status_root_v1", 6.0),
    }
    target = subtype_targets.get(service_access_subtype)
    if target is None:
        return candidates

    target_id, boost = target
    adjusted = []
    changed = False
    for candidate in candidates:
        updated = dict(candidate)
        if candidate["card"].get("id") == target_id:
            updated["score"] = round(candidate["score"] + boost, 4)
            changed = True
        adjusted.append(updated)

    if not changed:
        return candidates

    adjusted.sort(key=lambda item: item["score"], reverse=True)
    return adjusted


def _build_ambiguous_complaint_procedure_response() -> dict[str, Any]:
    follow_up_question = "Խոսքը բուժաշխատողի վարքագծի՞, հիվանդանոցի ծառայության կամ կազմակերպման մա՞սին է, թե պարզապես ուզում եք իմանալ որտեղ կամ ինչպես բողոք ներկայացնել։"
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": f"Բողոքի ընթացակարգը կախված է բողոքի տեսակից։ {follow_up_question}",
        "follow_up_question": follow_up_question,
        "matched_card_id": None,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_generic_complaint_intent_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    return normalized in GENERIC_COMPLAINT_INTENT_PHRASES


def _is_explicit_complaint_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if normalized in EXPLICIT_COMPLAINT_CONTACT_PHRASES:
        return True
    if "թեժ գիծ" in normalized or "8003" in normalized:
        return True
    return "բողոք" in normalized and ("զանգ" in normalized or "հեռախոս" in normalized)


def _is_complaint_harm_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_HARM_CONTACT_INTENT_ANCHORS)
    has_provider_anchor = any(term in normalized for term in COMPLAINT_HARM_PROVIDER_ANCHORS)
    has_fault_anchor = any(term in normalized for term in COMPLAINT_HARM_FAULT_ANCHORS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_HARM_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_provider_anchor and has_fault_anchor and not has_disqualifier


def _is_complaint_misconduct_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_MISCONDUCT_CONTACT_INTENT_ANCHORS)
    has_provider_anchor = any(term in normalized for term in COMPLAINT_MISCONDUCT_PROVIDER_ANCHORS)
    has_behavior_anchor = any(term in normalized for term in COMPLAINT_MISCONDUCT_BEHAVIOR_ANCHORS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_MISCONDUCT_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_provider_anchor and has_behavior_anchor and not has_disqualifier


def _is_complaint_denied_service_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_DENIED_SERVICE_CONTACT_INTENT_ANCHORS)
    has_refusal_anchor = any(term in normalized for term in COMPLAINT_DENIED_SERVICE_REFUSAL_ANCHORS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_DENIED_SERVICE_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_refusal_anchor and not has_disqualifier


def _is_complaint_duplicate_status_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_DUPLICATE_STATUS_CONTACT_INTENT_ANCHORS)
    has_status_marker = any(term in normalized for term in COMPLAINT_DUPLICATE_STATUS_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_DUPLICATE_STATUS_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_status_marker and not has_disqualifier


def _is_complaint_armed_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_ARMED_CONTACT_INTENT_ANCHORS)
    has_armed_marker = any(term in normalized for term in COMPLAINT_ARMED_VISIBILITY_MARKERS)
    has_record_marker = any(term in normalized for term in COMPLAINT_ARMED_RECORD_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_ARMED_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_armed_marker and has_record_marker and not has_disqualifier


def _is_complaint_record_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_RECORD_CONTACT_INTENT_ANCHORS)
    has_record_marker = any(term in normalized for term in COMPLAINT_RECORD_CONTACT_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_RECORD_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_record_marker and not has_disqualifier


def _is_complaint_inspection_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_INSPECTION_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_INSPECTION_SCOPE_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_INSPECTION_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and not has_disqualifier


def _is_complaint_medicine_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_MEDICINE_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_MEDICINE_SCOPE_MARKERS)
    has_refusal_marker = any(term in normalized for term in COMPLAINT_MEDICINE_REFUSAL_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_MEDICINE_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and has_refusal_marker and not has_disqualifier


def _is_complaint_referral_denial_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_REFERRAL_DENIAL_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_REFERRAL_DENIAL_SCOPE_MARKERS)
    has_refusal_marker = any(term in normalized for term in COMPLAINT_REFERRAL_DENIAL_REFUSAL_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_REFERRAL_DENIAL_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and has_refusal_marker and not has_disqualifier


def _is_complaint_waiting_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_WAITING_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_WAITING_SCOPE_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_WAITING_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and not has_disqualifier


def _is_complaint_pharmacy_service_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_PHARMACY_SERVICE_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_PHARMACY_SERVICE_SCOPE_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_PHARMACY_SERVICE_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and not has_disqualifier


def _is_complaint_investigation_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in COMPLAINT_INVESTIGATION_CONTACT_INTENT_ANCHORS)
    has_scope_marker = any(term in normalized for term in COMPLAINT_INVESTIGATION_SCOPE_MARKERS)
    has_refusal_marker = any(term in normalized for term in COMPLAINT_INVESTIGATION_REFUSAL_MARKERS)
    has_disqualifier = any(term in normalized for term in COMPLAINT_INVESTIGATION_CONTACT_DISQUALIFIERS)

    return has_contact_intent and has_scope_marker and has_refusal_marker and not has_disqualifier


def _build_complaint_contact_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_2_official_complaint_channels")
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Բողոքի համար կարող եք օգտվել պաշտոնական թեժ գծից կամ կապի համարներից։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": "complaint_2_official_complaint_channels",
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _build_provider_misconduct_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_40_provider_misconduct")
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Եթե բողոքը վերաբերում է բուժաշխատողի վարքագծին կամ մասնագիտական էթիկային, կիրառվում է համապատասխան նեղ ընթացակարգը։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": "complaint_40_provider_misconduct",
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _build_denied_service_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_refusal_denied_service_v2")
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": "Մերժման դեպքում նախ պետք է հասկանալ՝ ինչ ծառայություն են մերժել և ինչ հիմնավորում են տվել։ Գրե՛ք՝ ինչ ծառայություն են մերժել կամ ինչո՞ւ չեն սպասարկել։",
        "follow_up_question": "Ի՞նչ ծառայություն են մերժել կամ ինչո՞ւ չեն սպասարկել։",
        "matched_card_id": card.get("id") if card else "complaint_refusal_denied_service_v2",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_refusal_denied_service_v2",
            "pending_field": "refusal_context",
            "collected_fields": {},
        },
    })


def _build_duplicate_status_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_duplicate_charge_or_wrong_payment_status_v1")
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": "Նախ պետք է հասկանալ՝ խոսքը կրկնակի գանձմա՞ն մասին է, թե վճարման տվյալներն են սխալ երևում։ Գրե՛ք՝ խոսքը կրկնակի գանձմա՞ն մասին է, թե վճարման տվյալներն են սխալ երևում։",
        "follow_up_question": "Գրե՛ք՝ խոսքը կրկնակի գանձմա՞ն մասին է, թե վճարման տվյալներն են սխալ երևում։",
        "matched_card_id": card.get("id") if card else "complaint_duplicate_charge_or_wrong_payment_status_v1",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_duplicate_charge_or_wrong_payment_status_v1",
            "pending_field": "problem_type",
            "collected_fields": {},
        },
    })


def _build_armed_visibility_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("technical_armed_visibility_issue_v1")
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": "Եթե տվյալը ArMed-ում չի երևում, նախ պետք է հասկանալ՝ կոնկրետ ինչ տվյալ պետք է երևար։ Գրե՛ք՝ ArMed-ում ինչ տվյալ պետք է երևար՝ դեղատոմս, ծառայություն, գրառում, թե այլ բան։",
        "follow_up_question": "Գրե՛ք՝ ArMed-ում ինչ տվյալ պետք է երևար՝ դեղատոմս, ծառայություն, գրառում, թե այլ բան։",
        "matched_card_id": card.get("id") if card else "technical_armed_visibility_issue_v1",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "technical_armed_visibility_issue_v1",
            "pending_field": "armed_missing_item",
            "collected_fields": {},
        },
    })


def _build_record_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_missing_or_wrong_record_v1")
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": "Նախ պետք է հասկանալ՝ կոնկրետ ինչ գրառում կամ տվյալ է բացակայում կամ սխալ երևում։ Գրե՛ք՝ կոնկրետ ի՞նչ գրառում կամ տվյալ է բացակայում կամ սխալ երևում։",
        "follow_up_question": "Կոնկրետ ի՞նչ գրառում կամ տվյալ է բացակայում կամ սխալ երևում։",
        "matched_card_id": card.get("id") if card else "complaint_missing_or_wrong_record_v1",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_missing_or_wrong_record_v1",
            "pending_field": "record_problem_type",
            "collected_fields": {},
        },
    })


def _build_inspection_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_29_inspection")
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Եթե բողոքը վերաբերում է հիվանդանոցի ծառայությանը, կազմակերպմանը կամ վարչական հարցին, կիրառվում է համապատասխան պաշտոնական բողոքարկման ընթացակարգը։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": card.get("id") if card else "complaint_29_inspection",
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _build_medicine_not_provided_complaint_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_medicine_not_provided_v1")
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": "Եթե դեղը դուրս է գրված, բայց չեն տրամադրել, նախ պետք է պարզել՝ որ դեղի մասին է խոսքը և որտեղ այն չեն տվել։ Գրե՛ք դեղի անվանումը, դեղաչափը և ձևը։",
        "follow_up_question": "Գրե՛ք դեղի անվանումը, դեղաչափը և ձևը։",
        "matched_card_id": card.get("id") if card else "complaint_medicine_not_provided_v1",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_medicine_not_provided_v1",
            "pending_field": "medicine_name_details",
            "collected_fields": {},
        },
    })


def _get_structured_or_approved_direct_answer(card: dict | None, fallback: str) -> str:
    if not card:
        return fallback

    answer = card.get("approved_answer") or fallback
    structured = card.get("structured_answer")
    if isinstance(structured, dict):
        policy_parts = [structured.get(key, "").strip() for key in STRUCTURED_DIRECT_POLICY_KEYS if isinstance(structured.get(key), str) and structured.get(key).strip()]
        next_parts = [structured.get(key, "").strip() for key in STRUCTURED_DIRECT_NEXT_KEYS if isinstance(structured.get(key), str) and structured.get(key).strip()]
        structured_answer = " ".join(policy_parts + next_parts).strip()
        if structured_answer:
            answer = structured_answer
    return answer


def _is_mixed_entitlement_referral_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_entitlement_signal = any(term in normalized for term in MIXED_ENTITLEMENT_SIGNALS)
    has_referral_signal = any(term in normalized for term in MIXED_REFERRAL_SIGNALS)
    has_concrete_anchor = any(term in normalized for term in MIXED_CONCRETE_SERVICE_ANCHORS)

    if not (has_entitlement_signal and has_referral_signal):
        return False

    return not has_concrete_anchor


def _build_mixed_entitlement_referral_response() -> dict[str, Any]:
    follow_up_question = "Ճշտե՞նք՝ ուզում եք հասկանալ ով է օգտվում անվճար բուժօգնությունից, թե տվյալ ծառայության համար ուղեգիր պե՞տք է։"
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": f"Այստեղ խառնված են անվճար բուժօգնության իրավունքը և ուղեգրի հարցը։ {follow_up_question}",
        "follow_up_question": follow_up_question,
        "matched_card_id": None,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_ambiguous_payment_visibility_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    return normalized in AMBIGUOUS_PAYMENT_VISIBILITY_PHRASES


def _build_ambiguous_payment_visibility_response() -> dict[str, Any]:
    follow_up_question = "Ճշտե՞նք՝ վճարումն ընդհանրապես չի երևում համակարգում, թե վճարել եք, բայց կարգավիճակը սխալ է ցույց տրվում։"
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": f"Այստեղ պետք է ճշտել՝ խոսքը համակարգում չերևացող վճարմա՞ն, թե սխալ ցուցադրվող վճարման կարգավիճակի մասին է։ {follow_up_question}",
        "follow_up_question": follow_up_question,
        "matched_card_id": None,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_medicine_state_list_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_list_anchor = any(term in normalized for term in MEDICINE_STATE_LIST_ANCHORS)
    has_query_anchor = any(term in normalized for term in MEDICINE_STATE_LIST_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in MEDICINE_STATE_LIST_DISQUALIFIERS)
    has_eligibility_disqualifier = any(term in normalized for term in MEDICINE_STATE_LIST_ELIGIBILITY_DISQUALIFIERS)

    return has_list_anchor and has_query_anchor and not has_disqualifier and not has_eligibility_disqualifier


def _build_medicine_state_list_response() -> dict[str, Any]:
    card = get_card_by_id(MEDICINE_STATE_LIST_OWNER_ID)
    follow_up_question = "Նշե՛ք դեղի ճշգրիտ անվանումը, դեղաչափը և ձևը՝ օրինակ 500մգ դեղապատիճ։"
    answer = (
        "Պետության ցանկում ներառված լինելը կախված է դեղի ճշգրիտ անվանումից, "
        f"դեղաչափից և ձևից։ {follow_up_question}"
    )
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": answer,
        "follow_up_question": follow_up_question,
        "matched_card_id": card.get("id") if card else MEDICINE_STATE_LIST_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_pharmacy_oversight_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_control_anchor = "վերահսկ" in normalized
    has_subject_anchor = any(term in normalized for term in ("դեղատ", "դեղերի որակ", "որակը", "տրամադրում"))
    has_disqualifier = any(term in normalized for term in PHARMACY_OVERSIGHT_DISQUALIFIERS)

    return has_control_anchor and has_subject_anchor and not has_disqualifier


def _build_pharmacy_oversight_response() -> dict[str, Any]:
    card = get_card_by_id(PHARMACY_OVERSIGHT_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Դեղերի որակի և տրամադրման վերահսկողությունը իրականացվում է օրենքով սահմանված կարգով։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": card.get("id") if card else PHARMACY_OVERSIGHT_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_confidentiality_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_core_anchor = any(term in normalized for term in CONFIDENTIALITY_CORE_ANCHORS)
    has_query_anchor = any(term in normalized for term in CONFIDENTIALITY_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in CONFIDENTIALITY_DISQUALIFIERS)

    return has_core_anchor and has_query_anchor and not has_disqualifier


def _build_confidentiality_response() -> dict[str, Any]:
    card = get_card_by_id(CONFIDENTIALITY_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Բժշկական գաղտնիությունը և անձնական տվյալների պաշտպանությունը ապահովվում են օրենքով սահմանված կարգով։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": card.get("id") if card else CONFIDENTIALITY_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_foreign_citizen_legal_basis_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_foreign_anchor = any(term in normalized for term in FOREIGN_CITIZEN_ANCHORS)
    has_legal_anchor = any(term in normalized for term in FOREIGN_CITIZEN_LEGAL_ANCHORS)
    has_healthcare_anchor = any(term in normalized for term in FOREIGN_CITIZEN_HEALTHCARE_ANCHORS)
    has_disqualifier = any(term in normalized for term in FOREIGN_CITIZEN_LEGAL_DISQUALIFIERS)

    return has_foreign_anchor and has_legal_anchor and has_healthcare_anchor and not has_disqualifier


def _build_foreign_citizen_legal_basis_response() -> dict[str, Any]:
    card = get_card_by_id(FOREIGN_CITIZEN_LEGAL_BASIS_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Օտարերկրյա քաղաքացիների բժշկական օգնության իրավական հիմքը սահմանվում է ՀՀ օրենսդրությամբ և միջազգային պայմանագրերով։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": card.get("id") if card else FOREIGN_CITIZEN_LEGAL_BASIS_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_provider_liability_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_core_anchor = any(term in normalized for term in PROVIDER_LIABILITY_CORE_ANCHORS)
    has_provider_anchor = any(term in normalized for term in PROVIDER_LIABILITY_PROVIDER_ANCHORS)
    has_disqualifier = any(term in normalized for term in PROVIDER_LIABILITY_DISQUALIFIERS)

    return has_core_anchor and has_provider_anchor and not has_disqualifier


def _build_provider_liability_response() -> dict[str, Any]:
    card = get_card_by_id(PROVIDER_LIABILITY_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Բուժաշխատողի կամ բժշկական օգնություն իրականացնողի մեղքով վնաս պատճառելու դեպքում պատասխանատվությունը սահմանվում է ՀՀ օրենսդրությամբ։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": card.get("id") if card else PROVIDER_LIABILITY_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _build_card_decision_response(card_id: str, user_text: str, collected_fields: dict[str, Any] | None = None) -> dict[str, Any]:
    card = get_card_by_id(card_id)
    if not card:
        return validate_response({
            "status": "ok",
            "action": "escalate_true_gap",
            "answer": "Այս պահին հստակ պատասխանը չի գտնվել։",
            "follow_up_question": None,
            "matched_card_id": None,
            "escalation_reason": "true_kb_gap",
            "state": {
                "pending_card_id": None,
                "pending_field": None,
                "collected_fields": {},
            },
        })

    seeded_fields = _seed_inferable_required_fields(card, user_text, collected_fields or {})
    decision = decide(
        user_text=user_text,
        candidates=[{"card": card, "score": 10.0}],
        collected_fields=seeded_fields,
    )
    response = build_response(
        decision=decision,
        collected_fields=seeded_fields,
        user_text=user_text,
    )
    return validate_response(response)


def _is_explicit_eligibility_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_query_anchor = any(term in normalized for term in EXPLICIT_ELIGIBILITY_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in EXPLICIT_ELIGIBILITY_DISQUALIFIERS)
    return has_query_anchor and not has_disqualifier


def _build_explicit_eligibility_response(user_text: str) -> dict[str, Any]:
    normalized = normalize_text(user_text)
    seeded_fields: dict[str, Any] = {}
    if any(term in normalized for term in ("պետպատվ", "անվճար բուժօգն", "արտոնյալ բուժօգն", "շահառ")):
        seeded_fields["benefit_scope"] = "general_coverage"
    return _build_card_decision_response("eligibility_status_coverage_root_v1", user_text, seeded_fields)


def _is_general_medicine_coverage_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_medicine_anchor = any(term in normalized for term in GENERAL_MEDICINE_COVERAGE_ANCHORS)
    has_query_anchor = any(term in normalized for term in GENERAL_MEDICINE_COVERAGE_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in GENERAL_MEDICINE_COVERAGE_DISQUALIFIERS)
    return has_medicine_anchor and has_query_anchor and not has_disqualifier


def _build_general_medicine_coverage_response(user_text: str) -> dict[str, Any]:
    return _build_card_decision_response(
        "medicine_coverage_exact_name_dosage_form_v2",
        user_text,
    )


def _is_armed_visibility_issue_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_armed_anchor = any(term in normalized for term in COMPLAINT_ARMED_VISIBILITY_MARKERS)
    has_issue_marker = any(term in normalized for term in ARMED_VISIBILITY_ISSUE_MARKERS)
    has_target_marker = any(term in normalized for term in ARMED_VISIBILITY_TARGET_MARKERS)
    has_disqualifier = any(term in normalized for term in ARMED_VISIBILITY_ISSUE_DISQUALIFIERS)
    return has_armed_anchor and has_issue_marker and has_target_marker and not has_disqualifier


def _is_record_issue_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_record_marker = any(term in normalized for term in RECORD_ISSUE_MARKERS)
    has_issue_marker = any(term in normalized for term in RECORD_ISSUE_QUERY_MARKERS)
    has_disqualifier = any(term in normalized for term in RECORD_ISSUE_DISQUALIFIERS)
    return has_record_marker and has_issue_marker and not has_disqualifier


def _is_duplicate_status_issue_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_issue_marker = any(term in normalized for term in DUPLICATE_STATUS_ISSUE_MARKERS)
    has_disqualifier = any(term in normalized for term in DUPLICATE_STATUS_ISSUE_DISQUALIFIERS)
    return has_issue_marker and not has_disqualifier


def _is_specialist_referral_status_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_specialist_anchor = any(term in normalized for term in SPECIALIST_REFERRAL_STATUS_ANCHORS)
    has_process_anchor = any(term in normalized for term in SPECIALIST_REFERRAL_PROCESS_ANCHORS)
    has_disqualifier = any(term in normalized for term in SPECIALIST_REFERRAL_STATUS_DISQUALIFIERS)

    return has_specialist_anchor and has_process_anchor and not has_disqualifier


def _build_specialist_referral_status_response(user_text: str) -> dict[str, Any]:
    card = get_card_by_id("service_referral_status_root_v1")
    if not card:
        return validate_response({
            "status": "ok",
            "action": "escalate_true_gap",
            "answer": "Այս պահին հստակ պատասխանը չի գտնվել։",
            "follow_up_question": None,
            "matched_card_id": None,
            "escalation_reason": "true_kb_gap",
            "state": {
                "pending_card_id": None,
                "pending_field": None,
                "collected_fields": {},
            },
        })

    collected_fields: dict[str, Any] = {"service_type": "specialist"}
    collected_fields = _seed_inferable_required_fields(card, user_text, collected_fields)
    decision = decide(
        user_text=user_text,
        candidates=[{"card": card, "score": 10.0}],
        collected_fields=collected_fields,
    )
    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
        user_text=user_text,
    )
    return validate_response(response)


def _is_mri_ct_requirements_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_service_anchor = any(term in normalized for term in MRI_CT_REQUIREMENTS_ANCHORS)
    has_query_anchor = any(term in normalized for term in MRI_CT_REQUIREMENTS_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in MRI_CT_REQUIREMENTS_DISQUALIFIERS)

    return has_service_anchor and has_query_anchor and not has_disqualifier


def _build_mri_ct_requirements_response(user_text: str) -> dict[str, Any]:
    card = get_card_by_id("service_referral_status_root_v1")
    if not card:
        return validate_response({
            "status": "ok",
            "action": "escalate_true_gap",
            "answer": "Այս պահին հստակ պատասխանը չի գտնվել։",
            "follow_up_question": None,
            "matched_card_id": None,
            "escalation_reason": "true_kb_gap",
            "state": {
                "pending_card_id": None,
                "pending_field": None,
                "collected_fields": {},
            },
        })

    normalized = normalize_text(user_text)
    service_type = "mri"
    if any(term in normalized for term in ("կտ", "ct", "համակարգչային տոմոգրաֆիա", "կոմպյուտերային տոմոգրաֆիա")):
        service_type = "ct"

    collected_fields: dict[str, Any] = {"service_type": service_type}
    collected_fields = _seed_inferable_required_fields(card, user_text, collected_fields)
    decision = decide(
        user_text=user_text,
        candidates=[{"card": card, "score": 10.0}],
        collected_fields=collected_fields,
    )
    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
        user_text=user_text,
    )
    return validate_response(response)


def _is_mri_ct_routing_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_service_anchor = any(term in normalized for term in MRI_CT_REQUIREMENTS_ANCHORS)
    has_query_anchor = any(term in normalized for term in MRI_CT_ROUTING_QUERY_ANCHORS)
    has_disqualifier = any(term in normalized for term in MRI_CT_ROUTING_DISQUALIFIERS)
    return has_service_anchor and has_query_anchor and not has_disqualifier


def _build_mri_ct_routing_response(user_text: str) -> dict[str, Any]:
    return _build_card_decision_response("routing_referral_where_to_go_v2", user_text)


def _is_explicit_admission_process_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_admission_anchor = any(term in normalized for term in ADMISSION_PROCESS_ANCHORS)
    has_question_anchor = any(term in normalized for term in ADMISSION_PROCESS_QUESTION_ANCHORS)
    has_referral_service_anchor = any(term in normalized for term in REFERRAL_STATUS_SERVICE_ANCHORS)
    has_routing_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_ROUTING_DISQUALIFIERS)
    has_coverage_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_COVERAGE_DISQUALIFIERS)
    has_dispute_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_DISPUTE_DISQUALIFIERS)
    has_medical_risk_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_MEDICAL_RISK_DISQUALIFIERS)

    return (
        has_admission_anchor
        and has_question_anchor
        and not has_referral_service_anchor
        and not has_routing_disqualifier
        and not has_coverage_disqualifier
        and not has_dispute_disqualifier
        and not has_medical_risk_disqualifier
    )


def _is_admission_requirements_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_admission_anchor = any(term in normalized for term in ADMISSION_PROCESS_ANCHORS)
    has_requirements_anchor = any(term in normalized for term in ADMISSION_REQUIREMENTS_QUESTION_ANCHORS)
    has_routing_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_ROUTING_DISQUALIFIERS)
    has_coverage_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_COVERAGE_DISQUALIFIERS)
    has_dispute_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_DISPUTE_DISQUALIFIERS)
    has_medical_risk_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_MEDICAL_RISK_DISQUALIFIERS)

    return (
        has_admission_anchor
        and has_requirements_anchor
        and not has_routing_disqualifier
        and not has_coverage_disqualifier
        and not has_dispute_disqualifier
        and not has_medical_risk_disqualifier
    )


def _is_admission_policy_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_admission_anchor = any(term in normalized for term in ADMISSION_PROCESS_ANCHORS)
    has_policy_anchor = any(term in normalized for term in ADMISSION_POLICY_QUESTION_ANCHORS)
    has_routing_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_ROUTING_DISQUALIFIERS)
    has_coverage_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_COVERAGE_DISQUALIFIERS)
    has_dispute_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_DISPUTE_DISQUALIFIERS)
    has_medical_risk_disqualifier = any(term in normalized for term in ADMISSION_PROCESS_MEDICAL_RISK_DISQUALIFIERS)

    return (
        has_admission_anchor
        and has_policy_anchor
        and not has_routing_disqualifier
        and not has_coverage_disqualifier
        and not has_dispute_disqualifier
        and not has_medical_risk_disqualifier
    )


def _build_admission_process_response(user_text: str) -> dict[str, Any]:
    card = get_card_by_id("service_admission_type_root_v1")
    normalized = normalize_text(user_text)

    service_type = None
    if any(term in normalized for term in ("վիրահատ", "surgery", "operation")):
        service_type = "surgery"
    elif any(term in normalized for term in ("հիվանդանոց ընդուն", "հիվանդանոց պառկ", "հոսպիտալաց", "ստացիոնար", "պառկեմ հիվանդանոց")):
        service_type = "hospitalization"

    collected_fields: dict[str, Any] = {}
    if service_type is not None:
        collected_fields["service_type"] = service_type

    if service_type is None:
        pending_field = "service_type"
        follow_up_question = card.get("field_questions", {}).get("service_type", "Խոսքը հոսպիտալացմա՞ն մասին է, թե վիրահատության։")
        answer = f"Ընդունման կարգը կախված է նրանից՝ խոսքը հոսպիտալացմա՞ն մասին է, թե վիրահատության։ {follow_up_question}"
    else:
        admission_type = None
        has_planned = any(term in normalized for term in ("պլանային", "նախապես", "պլանավորված", "շտապ չէ", "ոչ շտապ"))
        has_emergency = any(term in normalized for term in ("անհետաձգելի", "շտապ վիրահատ", "շտապ ընդուն"))
        if has_planned and not has_emergency:
            admission_type = "planned"
        elif has_emergency and not has_planned:
            admission_type = "emergency"

        if admission_type is not None:
            collected_fields["admission_type"] = admission_type
            answer = None
            for rule in card.get("answer_rules", []):
                when = rule.get("when", {})
                if all(collected_fields.get(key) == value for key, value in when.items()):
                    answer = rule.get("answer")
                    break

            return validate_response({
                "status": "ok",
                "action": "direct_answer",
                "answer": answer or card.get("approved_answer"),
                "follow_up_question": None,
                "matched_card_id": "service_admission_type_root_v1",
                "escalation_reason": None,
                "state": {
                    "pending_card_id": None,
                    "pending_field": None,
                    "collected_fields": {},
                },
            })

        pending_field = "admission_type"
        follow_up_question = card.get("field_questions", {}).get("admission_type", "Դեպքը շտապ՞ է, թե պլանային։")
        answer = f"Այս դեպքում ընդունման կարգը կախված է նրանից՝ դեպքը շտապ՞ է, թե պլանային։ {follow_up_question}"

    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": answer,
        "follow_up_question": follow_up_question,
        "matched_card_id": "service_admission_type_root_v1",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "service_admission_type_root_v1",
            "pending_field": pending_field,
            "collected_fields": collected_fields,
        },
    })


def _is_polyclinic_transfer_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_institution_anchor = any(term in normalized for term in POLYCLINIC_TRANSFER_INSTITUTION_ANCHORS)
    has_change_anchor = any(term in normalized for term in POLYCLINIC_TRANSFER_CHANGE_ANCHORS)
    has_disqualifier = any(term in normalized for term in POLYCLINIC_TRANSFER_DISQUALIFIERS)

    return has_institution_anchor and has_change_anchor and not has_disqualifier


def _build_polyclinic_transfer_response() -> dict[str, Any]:
    card = get_card_by_id(POLYCLINIC_TRANSFER_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Եթե ուզում եք փոխել պոլիկլինիկան կամ ընտանեկան բժշկին, պետք է առաջնորդվել գործող կցագրման կարգով։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": POLYCLINIC_TRANSFER_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_family_doctor_transfer_refusal_contact_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_contact_intent = any(term in normalized for term in FAMILY_DOCTOR_TRANSFER_REFUSAL_CONTACT_INTENT_ANCHORS)
    has_scope_anchor = any(term in normalized for term in FAMILY_DOCTOR_TRANSFER_SCOPE_ANCHORS)
    has_change_anchor = any(term in normalized for term in FAMILY_DOCTOR_TRANSFER_CHANGE_ANCHORS)
    has_refusal_anchor = any(term in normalized for term in FAMILY_DOCTOR_TRANSFER_REFUSAL_ANCHORS)
    has_disqualifier = any(term in normalized for term in FAMILY_DOCTOR_TRANSFER_REFUSAL_CONTACT_DISQUALIFIERS)

    return (
        has_contact_intent
        and has_scope_anchor
        and has_change_anchor
        and has_refusal_anchor
        and not has_disqualifier
    )


def _build_family_doctor_transfer_refusal_contact_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_refusal_denied_service_v2")
    follow_up_question = "Գրե՛ք՝ պոլիկլինիկա փոխելու՞ց կամ նոր պոլիկլինիկայում գրանցվելու՞ց են հրաժարվել, և ինչ պատճառ են ասել։"
    answer = (
        "Եթե պոլիկլինիկա փոխելու կամ նոր պոլիկլինիկայում գրանցվելու հարցում մերժում կա, "
        f"պետք է պարզել՝ ինչ են մերժել և ինչ պատճառ են նշել։ {follow_up_question}"
    )
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": answer,
        "follow_up_question": follow_up_question,
        "matched_card_id": card.get("id") if card else "complaint_refusal_denied_service_v2",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_refusal_denied_service_v2",
            "pending_field": "refusal_context",
            "collected_fields": {},
        },
    })


def _is_family_doctor_refusal_rule_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_registration_anchor = any(term in normalized for term in FAMILY_DOCTOR_REGISTRATION_ANCHORS)
    has_refusal_anchor = any(term in normalized for term in FAMILY_DOCTOR_REFUSAL_ANCHORS)
    has_rule_question_anchor = any(term in normalized for term in FAMILY_DOCTOR_REFUSAL_RULE_QUESTION_ANCHORS)
    has_transfer_disqualifier = any(term in normalized for term in FAMILY_DOCTOR_REGISTRATION_TRANSFER_DISQUALIFIERS)

    return (
        has_registration_anchor
        and has_refusal_anchor
        and has_rule_question_anchor
        and not has_transfer_disqualifier
        and "բողոք" not in normalized
    )


def _build_family_doctor_refusal_rule_response() -> dict[str, Any]:
    card = get_card_by_id(FAMILY_DOCTOR_REFUSAL_RULE_OWNER_ID)
    answer = _get_structured_or_approved_direct_answer(
        card,
        "Ընտանեկան բժիշկը կարող է հրաժարվել գրանցելուց միայն սահմանված հիմքերով։",
    )
    return validate_response({
        "status": "ok",
        "action": "direct_answer",
        "answer": answer,
        "follow_up_question": None,
        "matched_card_id": FAMILY_DOCTOR_REFUSAL_RULE_OWNER_ID,
        "escalation_reason": None,
        "state": {
            "pending_card_id": None,
            "pending_field": None,
            "collected_fields": {},
        },
    })


def _is_family_doctor_registration_refusal_question(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    if not normalized:
        return False

    has_registration_anchor = any(term in normalized for term in FAMILY_DOCTOR_REGISTRATION_ANCHORS)
    has_refusal_anchor = any(term in normalized for term in FAMILY_DOCTOR_REFUSAL_ANCHORS)
    has_transfer_disqualifier = any(term in normalized for term in FAMILY_DOCTOR_REGISTRATION_TRANSFER_DISQUALIFIERS)

    return has_registration_anchor and has_refusal_anchor and not has_transfer_disqualifier


def _build_family_doctor_registration_refusal_response() -> dict[str, Any]:
    card = get_card_by_id("complaint_refusal_denied_service_v2")
    follow_up_question = "Գրե՛ք՝ ընտանեկան բժշկի մոտ գրանցո՞ւմն են մերժել, և ինչ պատճառ են ասել։"
    answer = (
        "Եթե ընտանեկան բժշկի կամ պոլիկլինիկայի մակարդակում չեն գրանցում, "
        f"նախ պետք է հասկանալ՝ ինչ պատճառով են հրաժարվել։ {follow_up_question}"
    )
    return validate_response({
        "status": "ok",
        "action": "partial_answer_with_clarify",
        "answer": answer,
        "follow_up_question": follow_up_question,
        "matched_card_id": card.get("id") if card else "complaint_refusal_denied_service_v2",
        "escalation_reason": None,
        "state": {
            "pending_card_id": "complaint_refusal_denied_service_v2",
            "pending_field": "refusal_context",
            "collected_fields": {},
        },
    })


def _infer_worker_benefit_scope(user_text: str) -> str | None:
    normalized = normalize_text(user_text)

    if any(term in normalized for term in ("դեղորայք", "դեղ", "medicine")):
        return "medicine"

    if any(term in normalized for term in ("հետազոտություն", "վերլուծություն", "mri", "ct", "diagnostic")):
        return "diagnostic"

    if any(term in normalized for term in ("բուժօգնություն", "բուժում", "treatment")):
        return "treatment"

    return None


def _has_child_status_signal(user_text: str) -> bool:
    normalized = normalize_text(user_text)
    return any(term in normalized for term in ("երեխա", "երեխայի", "մինչև 18", "մինչեւ 18", "անչափահաս"))


def _infer_child_benefit_scope(user_text: str) -> str | None:
    normalized = normalize_text(user_text)

    if any(term in normalized for term in ("հետազոտ", "վերլուծ", "ախտորոշ", "diagnostic")):
        return "diagnostic"

    if any(term in normalized for term in ("դեղ", "դեղորայք", "medicine")):
        return "medicine"

    if "հիվանդանոց" in normalized:
        return "treatment"

    if "բուժում" in normalized:
        return "treatment"

    if any(term in normalized for term in ("ինչ է ծածկվում", "ինչ ծածկույթ", "բժշկական օգնություն", "անվճար բուժօգնություն", "ինչ իրավունք")):
        return "general_coverage"

    return None


def _seed_inferable_required_fields(card: dict | None, user_text: str, collected_fields: dict[str, Any]) -> dict[str, Any]:
    if not card:
        return collected_fields

    seeded = dict(collected_fields)

    if card.get("id") == "service_referral_status_root_v1":
        required_fields = card.get("required_fields", [])
        for field_name in required_fields:
            if seeded.get(field_name) not in (None, ""):
                continue
            matched_value = _match_field_values_from_card(field_name, user_text, card)
            if matched_value is not None:
                seeded[field_name] = matched_value

    if card.get("id") == "eligibility_status_coverage_root_v1":
        if seeded.get("status_group") in (None, ""):
            matched_status = _match_field_values_from_card("status_group", user_text, card)
            if matched_status is not None:
                seeded["status_group"] = matched_status
            elif _has_child_status_signal(user_text):
                seeded["status_group"] = "child"

        if seeded.get("status_group") == "worker_insured" and seeded.get("benefit_scope") in (None, ""):
            matched_scope = _infer_worker_benefit_scope(user_text)
            if matched_scope is not None:
                seeded["benefit_scope"] = matched_scope

        if seeded.get("status_group") == "child" and seeded.get("benefit_scope") in (None, ""):
            matched_scope = _infer_child_benefit_scope(user_text)
            if matched_scope is not None:
                seeded["benefit_scope"] = matched_scope

    return seeded


@app.get("/health")
def health():
    return {
        "status": "ok",
        "cards_loaded": len(load_all_cards()),
    }


@app.post("/chat")
def chat(request: ChatRequest):
    incoming_state = request.state or {}
    collected_fields = incoming_state.get("collected_fields", {})
    if not isinstance(collected_fields, dict):
        collected_fields = {}

    pending_card_id = incoming_state.get("pending_card_id")
    pending_field = incoming_state.get("pending_field")
    pending_card = get_card_by_id(pending_card_id) if pending_card_id else None

    use_pending_flow = False
    if pending_card and pending_field:
        use_pending_flow = should_continue_pending_flow(request.message, pending_field)

    if use_pending_flow:
        coerced_value = coerce_field_value(pending_field, request.message, pending_card)
        if coerced_value is not None:
            collected_fields[pending_field] = coerced_value
        candidates = get_top_candidates(request.message, top_k=5, forced_card=pending_card)
    else:
        collected_fields = {}
        candidates = get_top_candidates(request.message, top_k=5, forced_card=None)
        complaint_subtype = _infer_complaint_subtype(request.message)
        service_access_subtype = _infer_service_access_subtype(request.message)
        if _is_explicit_complaint_contact_question(request.message):
            response = _build_complaint_contact_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_harm_contact_question(request.message):
            response = _build_complaint_contact_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_misconduct_contact_question(request.message):
            response = _build_provider_misconduct_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_medicine_contact_question(request.message):
            response = _build_medicine_not_provided_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_referral_denial_contact_question(request.message):
            response = _build_denied_service_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_waiting_contact_question(request.message):
            response = _build_inspection_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_pharmacy_service_contact_question(request.message):
            response = _build_inspection_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_investigation_contact_question(request.message):
            response = _build_denied_service_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_denied_service_contact_question(request.message):
            response = _build_denied_service_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_duplicate_status_contact_question(request.message):
            response = _build_duplicate_status_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_armed_contact_question(request.message):
            response = _build_armed_visibility_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_record_contact_question(request.message):
            response = _build_record_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_complaint_inspection_contact_question(request.message):
            response = _build_inspection_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if complaint_subtype == "procedure":
            response = _build_ambiguous_complaint_procedure_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_generic_complaint_intent_question(request.message):
            response = _build_ambiguous_complaint_procedure_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_mixed_entitlement_referral_question(request.message):
            response = _build_mixed_entitlement_referral_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_ambiguous_payment_visibility_question(request.message):
            response = _build_ambiguous_payment_visibility_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_family_doctor_refusal_rule_question(request.message):
            response = _build_family_doctor_refusal_rule_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_family_doctor_registration_refusal_question(request.message):
            response = _build_family_doctor_registration_refusal_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_family_doctor_transfer_refusal_contact_question(request.message):
            response = _build_family_doctor_transfer_refusal_contact_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_polyclinic_transfer_question(request.message):
            response = _build_polyclinic_transfer_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_armed_visibility_issue_question(request.message):
            response = _build_armed_visibility_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_record_issue_question(request.message):
            response = _build_record_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_duplicate_status_issue_question(request.message):
            response = _build_duplicate_status_complaint_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_general_medicine_coverage_question(request.message):
            response = _build_general_medicine_coverage_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_medicine_state_list_question(request.message):
            response = _build_medicine_state_list_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_pharmacy_oversight_question(request.message):
            response = _build_pharmacy_oversight_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_confidentiality_question(request.message):
            response = _build_confidentiality_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_foreign_citizen_legal_basis_question(request.message):
            response = _build_foreign_citizen_legal_basis_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_provider_liability_question(request.message):
            response = _build_provider_liability_response()
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_explicit_eligibility_question(request.message):
            response = _build_explicit_eligibility_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_mri_ct_routing_question(request.message):
            response = _build_mri_ct_routing_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_specialist_referral_status_question(request.message):
            response = _build_specialist_referral_status_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_mri_ct_requirements_question(request.message):
            response = _build_mri_ct_requirements_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        if _is_admission_policy_question(request.message):
            response = _build_admission_process_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response

        if _is_admission_requirements_question(request.message):
            response = _build_admission_process_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response

        if _is_explicit_admission_process_question(request.message):
            response = _build_admission_process_response(request.message)
            append_request_log({
                "message": request.message,
                "top_candidates": [
                    {
                        "id": c["card"].get("id"),
                        "category": c["card"].get("category"),
                        "score": c["score"]
                    }
                    for c in candidates
                ],
                "action": response.get("action"),
                "matched_card_id": response.get("matched_card_id"),
                "follow_up_question": response.get("follow_up_question"),
                "escalation_reason": response.get("escalation_reason"),
                "state": response.get("state")
            })
            return response
        candidates = _apply_complaint_subtype_bias(candidates, complaint_subtype)
        candidates = _apply_service_access_bias(candidates, service_access_subtype)

    top_card = candidates[0]["card"] if candidates else None
    collected_fields = _seed_inferable_required_fields(top_card, request.message, collected_fields)

    decision = decide(
        user_text=request.message,
        candidates=candidates,
        collected_fields=collected_fields,
    )

    response = build_response(
        decision=decision,
        collected_fields=collected_fields,
        user_text=request.message,
    )

    response = validate_response(response)

    append_request_log({
        "message": request.message,
        "top_candidates": [
            {
                "id": c["card"].get("id"),
                "category": c["card"].get("category"),
                "score": c["score"]
            }
            for c in candidates
        ],
        "action": response.get("action"),
        "matched_card_id": response.get("matched_card_id"),
        "follow_up_question": response.get("follow_up_question"),
        "escalation_reason": response.get("escalation_reason"),
        "state": response.get("state")
    })

    return response

@app.post("/chat-v2")
def chat_v2(request: ChatRequest):
    response = run_controller_v2(
        message=request.message,
        state=request.state or {},
    )

    append_request_log({
        "message": request.message,
        "v2": True,
        "action": response.get("action"),
        "matched_family": response.get("matched_family"),
        "follow_up_question": response.get("follow_up_question"),
        "state": response.get("state"),
        "cited_sources": response.get("cited_sources"),
    })

    return response

