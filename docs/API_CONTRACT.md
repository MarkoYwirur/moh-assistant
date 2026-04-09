# API Contract

## Active endpoints

### `GET /health`

Purpose:
- simple service health check

Response:

```json
{
  "status": "ok",
  "cards_loaded": 685
}
```

### `POST /chat`

Purpose:
- accepts one citizen message and an optional conversation state
- returns a controlled action, answer text, and next-step state

## Request format

```json
{
  "message": "string",
  "state": {
    "pending_card_id": "string | null",
    "pending_field": "string | null",
    "collected_fields": {}
  }
}
```

Fields:
- `message`: required user message in Armenian or mixed wording
- `state`: optional state returned by the previous response

## Response schema

```json
{
  "status": "ok",
  "action": "direct_answer | clarify | partial_answer_with_clarify | partial_answer_with_next_step | escalate_safety | escalate_true_gap",
  "answer": "string",
  "follow_up_question": "string | null",
  "matched_card_id": "string | null",
  "escalation_reason": "string | null",
  "state": {
    "pending_card_id": "string | null",
    "pending_field": "string | null",
    "collected_fields": {}
  }
}
```

## Action types

### `direct_answer`
- the system has a strong enough match and enough required fields to answer directly

### `clarify`
- the system needs one missing field before it can answer

### `partial_answer_with_clarify`
- the system can give a bounded partial answer and ask one clarifying question

### `partial_answer_with_next_step`
- the system can give a bounded partial answer and a next-step instruction without asking a field question

### `escalate_safety`
- the system detected medical-advice or urgency wording and does not answer with policy guidance alone

### `escalate_true_gap`
- the system cannot safely answer because the question is outside current bounded coverage

## State object

### `pending_card_id`
- the live owner/card waiting for one follow-up field

### `pending_field`
- the specific field the system is trying to collect next

### `collected_fields`
- already captured values carried into the next request

## Example request / response pairs

### 1. Eligibility clarification

Request:

```json
{
  "message": "ովքեր են օգտվում անվճար բուժօգնությունից",
  "state": {}
}
```

Response:

```json
{
  "status": "ok",
  "action": "partial_answer_with_clarify",
  "answer": "Պետության կողմից երաշխավորված անվճար կամ արտոնյալ բուժօգնությունը վերաբերում է իրավասու խմբերին, և վերջնական պատասխանը կախված է ձեր կարգավիճակից։",
  "follow_up_question": "Ո՞ր կարգավիճակին եք պատկանում։",
  "matched_card_id": "eligibility_status_coverage_root_v1",
  "escalation_reason": null,
  "state": {
    "pending_card_id": "eligibility_status_coverage_root_v1",
    "pending_field": "status_group",
    "collected_fields": {}
  }
}
```

### 2. Service/admin complaint procedure

Request:

```json
{
  "message": "ինչպես բողոք ներկայացնել հիվանդանոցի ծառայության համար",
  "state": {}
}
```

Response:

```json
{
  "status": "ok",
  "action": "direct_answer",
  "answer": "Եթե բողոքը վերաբերում է հիվանդանոցի ծառայությանը, կազմակերպմանը կամ վարչական հարցին, այն կարող է քննվել առողջապահական և աշխատանքի տեսչական մարմնի կարգով, ոչ թե մասնագիտական էթիկայի ընթացակարգով։ Բողոքը կարող է ներկայացվել առձեռն, փոստով կամ էլեկտրոնային եղանակով, և այն պետք է ներառի բողոքողի տվյալները, ներկայացվող պահանջը և ըստ անհրաժեշտության կից փաստաթղթերը։ Եթե բողոքում կան շտկվող սխալներ, դրանք մատնացույց են արվում 1 աշխատանքային օրվա ընթացքում և տրվում է 3 օր շտկելու համար, իսկ ընթացք տրվելու դեպքում բողոքողը տեղեկացվում է 3 օրվա ընթացքում։",
  "follow_up_question": null,
  "matched_card_id": "complaint_29_inspection",
  "escalation_reason": null,
  "state": {
    "pending_card_id": null,
    "pending_field": null,
    "collected_fields": {}
  }
}
```

### 3. Ethics complaint procedure

Request:

```json
{
  "message": "բժշկի վարքագծի բողոք",
  "state": {}
}
```

Response:

```json
{
  "status": "ok",
  "action": "direct_answer",
  "answer": "Եթե բողոքը վերաբերում է բուժաշխատողի վարքագծին կամ մասնագիտական էթիկայի հնարավոր խախտմանը, հենց այս նեղ ընթացակարգն է կիրառվում։ Այս դեպքում քննվում են այն խախտումները, որոնք չեն նախատեսում քրեական կամ վարչական պատասխանատվություն, և դիմումը ներկայացվում է համապատասխան դաշտերով ու ժամկետով։ Եթե բողոքը վերաբերում է հիվանդանոցի ծառայությանը, կազմակերպմանը կամ այլ հարցի, պետք է օգտվել համապատասխան ոչ-էթիկական բողոքի ուղուց։",
  "follow_up_question": null,
  "matched_card_id": "complaint_40_provider_misconduct",
  "escalation_reason": null,
  "state": {
    "pending_card_id": null,
    "pending_field": null,
    "collected_fields": {}
  }
}
```

### 4. Ambiguous complaint procedure

Request:

```json
{
  "message": "ինչպես բողոք ներկայացնել",
  "state": {}
}
```

Response:

```json
{
  "status": "ok",
  "action": "partial_answer_with_clarify",
  "answer": "Բողոքի ընթացակարգը կախված է բողոքի տեսակից։ Խոսքը բուժաշխատողի վարքագծի՞, թե հիվանդանոցի ծառայության կամ կազմակերպման մասին է։",
  "follow_up_question": "Խոսքը բուժաշխատողի վարքագծի՞, թե հիվանդանոցի ծառայության կամ կազմակերպման մասին է։",
  "matched_card_id": null,
  "escalation_reason": null,
  "state": {
    "pending_card_id": null,
    "pending_field": null,
    "collected_fields": {}
  }
}
```

### 5. Safety escalation

Request:

```json
{
  "message": "ինչ անեմ եթե ջերմություն ունեմ",
  "state": {}
}
```

Response:

```json
{
  "status": "ok",
  "action": "escalate_safety",
  "answer": "Ես բժշկական խորհրդատվություն չեմ տալիս։ Եթե վիճակը շտապ է, զանգահարեք 103 կամ 112։",
  "follow_up_question": null,
  "matched_card_id": null,
  "escalation_reason": "safety_medical",
  "state": {
    "pending_card_id": null,
    "pending_field": null,
    "collected_fields": {}
  }
}
```

## Integration notes

- The backend is stateless unless the client sends back `state`.
- A client should persist the returned `state` between turns.
- A client should treat `action` as the primary UI control signal.
- `matched_card_id` is useful for analytics and QA, not required for end-user display.
