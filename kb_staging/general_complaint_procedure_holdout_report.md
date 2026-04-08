# General Complaint Procedure Holdout Report

## Decision

The broader general complaint procedure layer is **not insertion-ready** in the current local repo snapshot.

Why:
- the strongest exact procedural excerpts on disk are still HLIB-specific
- the current MEC packet is ethics-specific by design
- no second broader non-HLIB procedure source is present locally to validate a universal or ministry-wide complaint rule

## Current Scope Split

### MEC ethics procedure

- already live through `complaint_40_provider_misconduct`
- source packet: `kb_staging/complaint_procedure_ready.json`
- valid only for treatment of professional-conduct / ethics complaints

### HLIB non-ethics inspection procedure

- already live through `complaint_29_inspection`
- source packet: `kb_staging/non_ethics_complaint_procedure_ready.json`
- valid only for service / organization / administrative complaints handled under the inspection-body path

### General complaint procedure

- target for a future batch
- not yet insertion-ready
- currently supported only by review-needed candidates extracted from the HLIB procedure

## Best Local Candidates For Future Generalization

From `kb_staging/general_complaint_procedure_review.json`:
- filing methods
- required information
- correction timing
- forwarding outside jurisdiction
- three-day complainant notice
- anonymous / false complaint handling

These remain `review-needed` because they are still evidenced only inside the HLIB procedure.

## What Is Still Missing

At least one broader local source that is:
- not MEC-specific
- not HLIB-specific
- exact enough to support one or more of:
  - filing steps
  - required information
  - forwarding / escalation
  - response timeline
  - processing flow

## Safe Next Step

Do not insert a general complaint-procedure layer yet.

Next useful run:
1. search local raw sources or imported official extracts for a broader non-MEC, non-HLIB complaint procedure
2. cross-check any overlapping rule against the HLIB packet
3. promote only the overlaps that are supported by more than one local exact source
