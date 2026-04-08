# Complaint Procedure Holdout Report

## Freeze State

- Runtime unchanged in this run
- Validation baseline: `TOTAL_ERRORS=1`
- Regression baseline: green
- Demo pack baseline: green

## Decision

The OCR run for `kb_raw_sources/complaints/hlib_complaints_procedure.pdf` produced a usable non-ethics complaint-procedure packet.

What is insertion-ready now:
- the narrow Medical Ethics Commission / professional-conduct procedure
- the non-ethics HLIB complaint procedure captured in `kb_staging/non_ethics_complaint_procedure_ready.json`

What is still not insertion-ready:
- broader complaint guidance outside the HLIB path
- appendix material that remains noisy or over-specific for a core procedure layer

Reason:
- the HLIB complaints-procedure PDF is now OCR-readable enough for filing methods, required information, deadlines, forwarding, and post-submission handling
- some surrounding materials are still too thin, noisy, or scope-sensitive to insert blindly

## Source Split

### A. Ethics / professional-conduct procedure

#### Insertion-ready and already used

Source file:
- `kb_raw_sources/complaints_extracted/mec_submit_application.txt`

Exact excerpts:
- `1. Տվյալների Լրացում`
- `2. Խախտման դեպք`
- `3. Մանրամասնեք դեպքը`
- `4. Թվային կամ ձեռքով ստորագրություն`
- `Էթիկայի ենթադրյալ խախտման օրը, ամիսը, տարին`
- `Դիմումները կարող են ներկայացվել, եթե ենթադրյալ խախտման օրվանից չի անցել մեկ օրացուցային տարի`
- `Ձեր տվյալները ...`
- `Բուժաշխատողի տվյալները ...`

Source file:
- `kb_raw_sources/complaints_extracted/mec_home.txt`

Exact excerpts:
- `Էթիկայի հանձնաժողովը ... մեկ աշխատանքային օրվա ընթացքում ... ծանուցում է ...`
- `Էթիկայի հանձնաժողովում քննության են ենթակա բուժաշխատողի մասնագիտական էթիկայի կանոնների խախտումները ...`

Classification:
- `insertion-ready`

Reason:
- exact local excerpts
- narrow scope
- already mapped safely to the ethics complaint path only

### B. Non-ethics complaint procedure

#### Insertion-ready

Source files:
- `kb_raw_sources/complaints_extracted/hlib_complaints_procedure_ocr.txt`
- `kb_staging/non_ethics_complaint_procedure_extracted.txt`
- `kb_staging/non_ethics_complaint_procedure_ready.json`

Ready coverage now includes:
- filing methods
- required information
- missing-contact fallback
- correction timing
- out-of-jurisdiction forwarding
- complainant notification timing
- anonymous / false complaint handling
- high-risk inspection timing
- hearing / proceeding notice flow
- inspection-order notice timing

#### Review-needed

Source file:
- `kb_raw_sources/complaints_extracted/hlib_online_application.txt`

Exact excerpts:
- `Բողոքների ընդունման և հետագա ընթացք տալու կարգ`
- `Առցանց դիմում`
- `Ստորև առկա բոլոր դաշտերի լրացումը պարտադիր է:`

Classification:
- `review-needed`

Reason:
- these lines now support the HLIB packet contextually
- they are still too thin on their own for direct runtime insertion

#### Reject / blocked

Source file:
- `kb_raw_sources/complaints_extracted/hlib_complaints_procedure_ocr.txt`

Exact local note:
- `ԽՈՐՀՐԴԱՏՎՈՒԹՅԱՆ ԹԵՐԹԻԿ`

Classification:
- `reject`

Reason:
- appendix 1 remains too noisy for exact excerpt use

## Why Runtime Was Not Edited In That Run

That earlier run stopped correctly because the local evidence then available was too weak.

This OCR pass changes the evidence picture for the HLIB path only. Runtime still has not been edited in the current OCR run.

## Remaining Gaps

The repo still needs stronger exact local material for:

- broader complaint guidance outside the HLIB path
- cleaner appendix material if the consultation-sheet path ever becomes relevant
- any Ministry-level non-ethics complaint procedure that differs from the HLIB process

## Safe Next Step

The next useful run should:
1. review `kb_staging/non_ethics_complaint_procedure_ready.json`
2. map only the safe non-ethics HLIB subset into the complaints family
3. keep the MEC ethics path and hotline/contact ownership separate
