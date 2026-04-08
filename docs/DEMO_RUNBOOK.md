# Demo Runbook

## Before a demo

Run:

```powershell
py run_validate_kb_utf8.py
py run_regression.py
py -X utf8 scripts/run_demo_pack.py
```

## Canonical demo pack

The canonical phrase pack lives in:

- [demo/demo_phrase_pack.json](/c:/Users/Asus/Desktop/moh-assistant/demo/demo_phrase_pack.json)

The helper prints, for each phrase:

- top winner
- top 3 candidates
- action
- follow-up question
- demo status
- risk note

Interpret the statuses like this:

- `safe_to_demo`: use freely in the main walkthrough
- `safe_with_explanation`: use only if the operator is ready to explain the follow-up behavior
- `avoid_in_demo`: do not use as a main showcase phrase

## Safe to demo

- child eligibility coverage
- worker-insured eligibility
- referral-required MRI / lab / specialist questions
- hospitalization / surgery admission questions
- payment complaint and ArMed visibility complaint flows
- hotline and contact questions (`թեժ գիծ`, `8003`)

## Safe with explanation

- `այս դեղը ծածկվո՞ւմ է`
  - explain that the system routes correctly to medicine coverage, but still needs the exact medicine name, dosage, and form
- `երեխայի համար դեղ է ծածկվում`
  - explain that the system may ask for the exact medicine name, dosage, and form

## Avoid in demo

- avoid vague ad-lib medicine questions that do not make it clear a medicine is being asked about
- for the strongest medicine demo, still prefer a concrete medicine query

## Suggested demo order

1. eligibility
2. referral-status
3. admission-type
4. complaints / routing
5. contacts
6. medicines last, with an exact medicine example instead of generic wording

## Operator tips

- Prefer Armenian phrasing for Armenian demos.
- If the system asks a clarification question, answer it directly instead of rephrasing the original issue.
- Do not overclaim exact entitlement decisions; the live product is best at triage, clarification, and source-grounded guidance.
- On Windows, prefer `py -X utf8 scripts/run_demo_pack.py` so Armenian text prints correctly.
