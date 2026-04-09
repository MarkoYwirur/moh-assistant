# Deployment Boundaries

## What can be shown publicly

- eligibility clarification flows
- referral-dependent access guidance
- hospital admission vs surgery admission clarification
- complaint routing across ethics, service/admin, contact/help, and payment
- official contact/help facts already in the live KB
- controlled safety escalation behavior

## What stays internal

- internal staging packs, raw-source extraction files, and migration notes
- backup files and experimental controller/history files
- request logs and internal analytics identifiers
- KB build workflow and validation workflow details

## What kinds of questions must clarify

- questions that depend on one missing field such as status group, referral status, service type, or complaint type
- ambiguous complaint-procedure questions without enough context to distinguish ethics vs service/admin
- service questions where a partial answer is safe but one detail is still required

## What kinds of questions must escalate

- medical-advice or symptom-driven questions
- urgent/emergency wording
- true knowledge gaps outside current bounded coverage

## Known limitations

- the product does not make final case-level entitlement decisions
- generic medicine questions are weaker than exact medicine-name questions
- some broad mixed phrases still resolve to clarify instead of a direct answer, by design
- complaint procedures are separated into live bounded paths; they are not presented as one universal complaint workflow

## What should not be promised in sales conversations

- do not promise diagnosis or treatment advice
- do not promise automatic legal or administrative outcomes
- do not promise that every complaint type is fully covered by one shared procedure
- do not promise final eligibility determinations without user-specific official review
- do not position the product as a general chatbot that can answer any health question
