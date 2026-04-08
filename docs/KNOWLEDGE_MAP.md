# Knowledge Map

Use this as the quick anti-duplication map before adding new runtime facts.

## Eligibility root

- Runtime owner: `eligibility_status_coverage_root_v1`
- Purpose: status-based eligibility and broad benefit-scope clarification
- Good fit:
  - child / worker-insured / pensioner / disability / pregnancy / social-vulnerability eligibility
  - broad coverage, treatment, medicine, diagnostic eligibility by status
- Do not add here:
  - referral-only rules
  - “where do I go?” routing
  - exact medicine-name coverage
  - hospitalization vs surgery branching

## Referral-status root

- Runtime owner: `service_referral_status_root_v1`
- Purpose: whether a referral is needed or already present for a service
- Good fit:
  - MRI / CT / lab / specialist / child hospital referral logic
  - phrases that hinge on having or not having a referral
- Do not add here:
  - broad eligibility group rules
  - pure admission-type logic
  - complaint escalation channels

## Admission-type root

- Runtime owner: `service_admission_type_root_v1`
- Purpose: hospitalization vs surgery, planned vs urgent/emergency
- Good fit:
  - hospitalization coverage questions
  - surgery coverage questions
  - planned vs urgent admission questions
- Do not add here:
  - referral-only logic
  - eligibility category facts
  - medicine coverage phrasing

## Medicines

- Runtime owner: `medicine_coverage_exact_name_dosage_form_v2` plus exact medicine cards
- Purpose: exact medicine coverage lookup
- Good fit:
  - exact medicine names
  - questions that require name + dosage + form
- Do not add here:
  - broad benefit-category eligibility
  - complaint not-provided flows
  - generic health-service coverage policy

## Complaints and support

- Runtime owners:
  - `complaint_unexpected_payment_dispute_v2`
  - `complaint_refusal_denied_service_v2`
  - `complaint_medicine_not_provided_v1`
  - `complaint_missing_or_wrong_record_v1`
  - `technical_armed_visibility_issue_v1`
  - `complaint_duplicate_charge_or_wrong_payment_status_v1`
  - `complaint_2_official_complaint_channels`
- Purpose: complaint routing, escalation, correction paths, official contact/help channels
- Good fit:
  - unexpected payment
  - denied care
  - wrong record / missing record
  - ArMed visibility issues
  - official hotline/contact facts tied to complaint/help flows
- Do not add here:
  - pure service eligibility rules
  - exact medicine entitlement logic
  - generic referral-acquisition routing

## Routing

- Runtime owners:
  - `routing_referral_where_to_go_v2`
  - `routing_specialist_referral_confusion_v1`
- Purpose: “where do I go?” and referral-acquisition navigation
- Good fit:
  - how to get a referral
  - which doctor or place to approach
  - specialist navigation confusion
- Do not add here:
  - complaint hotlines unless the answer is truly routing-oriented
  - eligibility logic
  - exact service coverage decisions

## FAQ and reference-style content

- Runtime area: `faq.json`
- Purpose: informational answers that are not better owned by a live operational root
- Good fit:
  - narrow FAQ-style source-grounded facts
  - reference answers that do not control major runtime decision paths
- Do not add here:
  - facts already better owned by eligibility / referral / admission / complaints / medicines / routing

## Working rule

Before inserting a fact, ask:

1. Is this primarily eligibility, referral, admission, complaint, routing, medicine, or FAQ?
2. Which live root already owns that decision?
3. Does the phrasing anchor the right domain strongly enough?

If the destination is still unclear after that, hold the fact out instead of forcing it into runtime.
