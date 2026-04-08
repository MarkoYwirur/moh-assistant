# Next Source Backlog

Prioritized next source-grounded content batches to seek or ingest inside the frozen architecture.

1. Broader complaint procedure batch beyond MEC
   - target: complaints family
   - likely source type: formal complaint procedure pages / PDFs / official forms
   - citizen question: Where exactly should I complain, what details do I need to provide, and what happens after submission outside the narrow ethics path?
   - why high value: extends the now-live MEC procedure layer into broader complaint handling
   - insertion safety: medium
   - overlap risk: medium
   - review: medium

2. Rights and informed-consent contact batch
   - target: complaints / routing contact surfaces
   - likely source type: MOH rights pages, official help pages
   - citizen question: Where can I ask about my rights, consent, or unlawful refusal?
   - why high value: supports trustworthy positioning and complaint triage
   - insertion safety: medium
   - overlap risk: low
   - review: low

3. More adult eligibility / privileged-group detail batch
   - target: `eligibility_status_coverage_root_v1`
   - likely source type: legal PDFs on state-guaranteed or privileged hospital care
   - citizen question: Which groups qualify for free or privileged hospital care, and what conditions apply?
   - why high value: high citizen value and fits the live eligibility root cleanly
   - insertion safety: medium
   - overlap risk: low to medium
   - review: low

4. Narrow oncology referral batch
   - target: `service_referral_status_root_v1`
   - likely source type: legal PDFs like `legal-385.pdf`
   - citizen question: How do I get referred to a pediatric oncologist?
   - why high value: already sourced, but must stay specialist-specific
   - insertion safety: medium
   - overlap risk: medium
   - review: medium

5. Technical registry / ArMed clarification batch
   - target: technical complaint flows
   - likely source type: official ArMed / MOH support guidance
   - citizen question: What should I do if my referral or record is missing from the system?
   - why high value: practical issue with strong complaint-routing relevance
   - insertion safety: medium
   - overlap risk: medium
   - review: medium

6. Hospital admission and state-guarantee clarification batch
   - target: `service_admission_type_root_v1`, `eligibility_status_coverage_root_v1`
   - likely source type: legal PDFs on state-guaranteed hospital care
   - citizen question: When is hospital care free, and what depends on planned vs urgent admission?
   - why high value: extends existing admission root without reopening migration
   - insertion safety: medium
   - overlap risk: medium
   - review: medium

7. Specialist referral exception batch
   - target: `service_referral_status_root_v1`
   - likely source type: official referral rules / specialist-specific MOH excerpts
   - citizen question: Are there specialist cases that require a specific referring doctor?
   - why high value: helps narrow referral advice for high-friction specialist journeys
   - insertion safety: medium
   - overlap risk: medium
   - review: medium
