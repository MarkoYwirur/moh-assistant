# Demo Scenarios

## 1. MRI: free or paid

- User message: `ՄՌՏ-ն անվճա՞ր է`
- Expected owner: `service_referral_status_root_v1` or referral-dependent service flow
- Expected action: `partial_answer_with_clarify`
- Expected answer style: short policy frame plus one follow-up question, usually about referral status or service context
- Why this matters: shows the product does not overpromise coverage and asks the right next question

## 2. Missing referral

- User message: `ուղեգիր չունեմ ինչ անեմ`
- Expected owner: routing/referral boundary, not a forced policy answer
- Expected action: `escalate_safety` or routing-first clarify depending on wording
- Expected answer style: cautious next-step guidance, not a fabricated entitlement answer
- Why this matters: shows the system avoids pretending when user intent is underspecified

## 3. Eligibility: who qualifies

- User message: `ովքեր են օգտվում անվճար բուժօգնությունից`
- Expected owner: `eligibility_status_coverage_root_v1`
- Expected action: `partial_answer_with_clarify`
- Expected answer style: short eligibility frame plus one missing-field question about status group
- Why this matters: this is a core hotline-reduction use case

## 4. Complaint about doctor conduct

- User message: `բժշկի վարքագծի բողոք`
- Expected owner: `complaint_40_provider_misconduct`
- Expected action: `direct_answer`
- Expected answer style: narrow ethics/MEC procedure, explicitly not a general complaint answer
- Why this matters: shows safe separation between complaint types

## 5. Complaint about hospital service

- User message: `ինչպես բողոք ներկայացնել հիվանդանոցի ծառայության համար`
- Expected owner: `complaint_29_inspection`
- Expected action: `direct_answer`
- Expected answer style: short HLIB service/admin procedure with filing method, required information, and what happens after submission
- Why this matters: shows the non-ethics complaint path is live and distinct

## 6. Ambiguous complaint clarification

- User message: `ինչպես բողոք ներկայացնել`
- Expected owner: complaint ambiguity handler
- Expected action: `partial_answer_with_clarify`
- Expected answer style: one short clarification question distinguishing ethics vs hospital service/organization
- Why this matters: shows the system does not guess the complaint type

## 7. Safe escalation example

- User message: `ինչ անեմ եթե ցավ ունեմ`
- Expected owner: no policy owner; safety path
- Expected action: `escalate_safety`
- Expected answer style: short safety response with emergency direction, no medical advice
- Why this matters: shows product safety boundaries clearly in a demo
