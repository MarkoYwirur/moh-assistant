# Product Overview

## What the product is

This product is a controlled Armenian healthcare guidance backend. It is built to help citizen-facing channels route questions into the right policy domain, return bounded answers when the knowledge base is grounded, and ask one focused follow-up question when one missing detail is needed.

It is meant for government and partner channels that need structured guidance, not open-ended autonomous reasoning.

## What it does well today

- Routes users into stable guidance domains such as eligibility, referrals, admissions, complaints, payment issues, ArMed visibility, and medicine coverage checks.
- Returns a small set of controlled actions rather than improvising free-form behavior:
  - `direct_answer`
  - `clarify`
  - `partial_answer_with_clarify`
  - `partial_answer_with_next_step`
  - `escalate_safety`
  - `escalate_true_gap`
- Uses lightweight conversation state so follow-up turns can collect one missing field at a time.
- Resets that lightweight state when the user clearly switches topics, instead of forcing the next question through the old clarify flow.
- Keeps shadow telemetry available for Phase 6 analysis without changing live owner selection.

## What is live right now

- The controlled routing engine is live and authoritative.
- The release-blocking benchmark is green for internal shadow-live use.
- Shadow telemetry exists for bounded Phase 6 analysis.
- Live adjudication override is not enabled.

## What it does not do

- It does not provide diagnosis or treatment advice.
- It does not make final personalized entitlement decisions.
- It does not act like a general-purpose chatbot that improvises policy answers.
- It does not provide generic medicine coverage answers without exact medicine details when those details are required.
- It does not run broad autonomous Phase 6 override logic in production.

## Why it is safer than a general chatbot

- It keeps major policy families separated instead of collapsing them into one answer style.
- It asks one bounded clarification question when one key field is missing.
- It falls back to controlled actions when the KB does not support a safe answer.
- It keeps sensitive complaint, eligibility, admission, and medicine flows grounded in explicit logic and KB content.

## Deployment positioning

Present this system as:

- a structured healthcare guidance layer
- a routing and clarification backend
- a controlled Armenian policy assistant for hotline-style questions

Do not present it as:

- fully autonomous policy adjudication
- a generic entitlement decision engine
- a free-form medical or legal assistant

## Honest current boundary

The product is pilot-ready for internal shadow-live usage because the stable routing layer is strong and the release-blocking benchmark is green. The unresolved exploratory Phase 6 surfaces remain bounded, monitored, and intentionally not live-overridden.
