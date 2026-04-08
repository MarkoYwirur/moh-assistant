# Anti-Duplication Notes

Use these rules before inserting any new official content.

## 1. Choose the decision owner first

- Eligibility question -> `eligibility_status_coverage_root_v1`
- Referral question -> `service_referral_status_root_v1`
- Admission-type question -> `service_admission_type_root_v1`
- Complaint or escalation question -> complaints family
- “Where do I go?” question -> routing family
- Exact medicine coverage question -> medicines

If ownership is unclear, hold the fact out instead of forcing it into runtime.

## 2. Do not duplicate the same fact across families

- A hotline/contact fact should usually have one runtime owner.
- A referral fact should not also become an eligibility fact unless the source truly states both and both are needed.
- A child-specific fact should stay narrow; do not restate it as a broad adult rule.

## 3. Avoid broad generic patterns

Do not add naked patterns like:

- `անվճար է`
- `ծածկվում է`
- `դիմեմ`
- `բողոք`
- `դեղ`

Anchor them to the exact domain:

- service
- status group
- referral
- hospital
- medicine
- hotline/contact

## 4. FAQ is not the default destination

Use FAQ only when:

- the fact is genuinely FAQ-like
- and it is not better owned by eligibility, referral, admission, complaints, routing, or medicines

## 5. Batch discipline

After each batch run:

1. `py run_validate_kb_utf8.py`
2. `py run_regression.py`
3. targeted phrase checks for the edited family
4. `py -X utf8 scripts/run_demo_pack.py` if the batch affects demo surfaces
