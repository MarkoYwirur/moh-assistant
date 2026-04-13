# Product State Note

This system is currently best described as a structured Armenian healthcare guidance assistant with a stable controlled engine, lightweight follow-up state, and Phase 6 shadow telemetry.

## What is stable

- eligibility clarification by status group and benefit scope
- referral-dependent service access guidance for MRI, CT, lab, and specialist flows
- hospitalization and admission clarification
- complaint routing for denial, payment issues, duplicate charge, missing record, ArMed visibility, and official complaint-contact questions
- bounded medicine coverage handling that asks for exact medicine details when needed
- family doctor registration and transfer FAQ coverage

## What changed in the latest cleanup sprint

- pending follow-up state now resets on clear topic switch instead of incorrectly consuming the next full question
- the validator-exposed broad child trigger in the eligibility root was narrowed
- regression coverage now includes topic-switch reset checks and CT canonicalization checks
- structured live-like scenarios now exercise real multi-turn `/chat` behavior with persisted state

## What remains intentionally bounded

- live Phase 6 adjudication override is still off
- exploratory/no-go surfaces remain shadow-only
- broad autonomous reasoning is not part of the live runtime

## What should be claimed externally

- strong routing and bounded follow-up questions
- controlled action outputs
- grounded healthcare guidance for supported policy areas
- internal shadow-live readiness with benchmarked protected owners

## What should not be claimed

- fully autonomous healthcare policy adjudication
- generic medicine coverage answers without exact medicine information
- personalized entitlement guarantees
- live semantic override across unresolved Phase 6 surfaces

## Recommended demo framing

- show category routing
- show one-step clarification
- show topic-switch reset working correctly
- show CT canonicalization behaving consistently
- avoid claiming that unresolved exploratory surfaces are already solved live
