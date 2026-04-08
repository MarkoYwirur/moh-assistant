# Product State Note

This system is now best described as a structured Armenian healthcare guidance assistant with frozen routing architecture and source-grounded KB expansion.

## What is live and reliable

- eligibility clarification by status group
- referral-dependent service access for MRI, CT, lab, specialist, and child hospital referral facts
- hospitalization vs surgery admission clarification
- complaints, payment issues, ArMed visibility issues, and routing to the right next step
- official hotline/contact facts already ingested into runtime

## What it handles well

- telling the user what category their problem belongs to
- asking the next useful clarification question
- distinguishing eligibility vs referral vs admission vs complaint vs routing
- giving source-grounded contact/help information

## What should not be overclaimed

- exact personalized entitlement decisions
- generic medicine coverage without an exact medicine name, dosage, and form
- provider-specific final coverage guarantees

## Demo strengths

- clear category routing
- clean follow-up questions
- stable migrated root architecture
- official hotline/contact answers

## Demo avoidances

- do not use the generic phrase `այս դեղը ծածկվո՞ւմ է`
- prefer concrete medicine examples

## What growth depends on next

- more narrow source-grounded facts inside the existing live roots
- better official contact / complaint procedure coverage
- more child-health and referral detail from official MOH materials
- continued discipline against reintroducing overlap or broad generic patterns
