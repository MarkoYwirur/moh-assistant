# KB Coverage Summary

Use this as the fast “what is already live?” checkpoint before adding new source-grounded facts.

## Major live roots

- `eligibility_status_coverage_root_v1`
  - owns status-based eligibility and benefit-scope clarification
  - already covers child eligibility, worker-insured eligibility, adult state-guaranteed free-care phrasing, and “who qualifies” questions
- `service_referral_status_root_v1`
  - owns referral-needed / referral-present logic
  - already covers MRI, CT, lab, specialist, and child hospital referral phrasing
- `service_admission_type_root_v1`
  - owns hospitalization vs surgery and planned vs urgent admission framing

## Other major live surfaces

- medicines
  - `medicine_coverage_exact_name_dosage_form_v2` plus exact medicine cards
  - use for exact drug coverage questions, not broad eligibility rules
- complaints and support
  - payment disputes, refusal/denial, missing or wrong record, ArMed visibility, duplicate charge / wrong payment status, official complaint/hotline contacts
  - narrow ethics/professional-conduct complaint procedure via Medical Ethics Commission
- routing
  - where to go for referral or specialist-navigation confusion
- FAQ
  - still a large live informational surface
  - use only when a fact is not more cleanly owned by an existing operational root

## Official source-grounded facts already inserted

- official hotline / contact facts
  - `թեժ գիծ`
  - `8003`
  - `060 808003`
  - `(060) 80 80 02`
  - `(010) 65 47 11`
  - `(010) 52 88 72`
  - child medical-aid complaint/contact routing
- child free-care facts
  - child hospital medical aid
  - child planned hospital-care phrasing support
  - child special diagnostics / difficult-access diagnostics
  - child hospital referral requirement
- adult eligibility / state-guarantee facts
  - state-guaranteed free or privileged hospital care applies to eligible groups
  - not all citizens qualify automatically
  - final eligibility depends on status and service type
- complaint procedure facts
  - Medical Ethics Commission complaint steps
  - required complainant / provider information for that narrow procedure
  - one-year filing deadline for that narrow procedure
  - one-working-day post-submission notification for that narrow procedure
  - HLIB non-ethics service/admin complaint procedure filing methods and required data
  - HLIB missing-contact fallback, anonymous/false complaint handling, fixable-error timing, forwarding, and three-day complainant notice wording

## Safe insertion guidance

- Add new eligibility-group or status-coverage facts into `eligibility_status_coverage_root_v1`.
- Add new referral-required / referral-present facts into `service_referral_status_root_v1`.
- Add hospitalization vs surgery / planned vs urgent facts into `service_admission_type_root_v1`.
- Add complaint/help-channel facts into complaints only if they are truly complaint/contact oriented.
- Keep complaint procedure facts narrow: the current live procedure layer is ethics/professional-conduct specific, not a universal Ministry complaint process.
- Add medicine facts only when they are exact-drug anchored.

## High-risk duplication zones

- Do not duplicate referral rules inside eligibility just because the user group is the same.
- Do not duplicate complaint/help contacts into routing or FAQ unless the destination clearly owns the question.
- Do not generalize the Medical Ethics Commission procedure to all complaints.
- Do not duplicate generic “covered/free” wording into medicines unless the phrase is really about an exact drug.
- Be cautious with child diagnostic phrasing additions because they can accidentally pull generic child-medicine demo wording toward eligibility.
- Be cautious with FAQ because it is still a large live informational surface and can overlap operational roots easily.
