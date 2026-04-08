# Source Registry

## Current logged batch

| Batch | Source | Destination | Status | Notes |
| --- | --- | --- | --- | --- |
| MOH batch 1 / Item 1 | MOH homepage navigation | `complaint_2_official_complaint_channels` | inserted | hotline `8003` |
| MOH batch 1 / Item 2 | `erexaneri petpatver.pdf` | `eligibility_status_coverage_root_v1` | inserted | child planned hospital + diagnostic by referral |
| MOH batch 1 / Item 3 | `erexaneri petpatver.pdf` | `complaint_2_official_complaint_channels` | inserted | child complaint contacts and hotline numbers |
| MOH batch 1 / Item 4 | `legal-417.pdf` | `eligibility_status_coverage_root_v1` | inserted | child free hospital care eligibility |
| MOH batch 1 / Item 5 | `legal-417.pdf` | `service_referral_status_root_v1` | inserted | child hospital care by AAP referral |
| MOH batch 1 / Item 6 | `degher.pdf` | `complaint_2_official_complaint_channels` | inserted | `8003`, `060 808003` |
| MOH batch 1 / Item 7 | `legal-385.pdf` | review-only | held out | narrow oncology routing candidate for a dedicated later pass |
| Overnight batch / Child hospital continuation | `erexaneri petpatver.pdf` | `eligibility_status_coverage_root_v1` | inserted | exact child planned hospital-care phrasing support |
| Overnight batch / Hotline clarification | `erexaneri petpatver.pdf` + `moh.am` | `complaint_2_official_complaint_channels` | inserted | added `(060) 80 80 02`, `(010) 65 47 11`, `(010) 52 88 72` phrase support |
| Overnight batch / Child diagnostics phrasing | `erexaneri petpatver.pdf` | `eligibility_status_coverage_root_v1` | reverted | strengthening phrases nudged a medicine demo surface; reverted to preserve runtime behavior |
| Complaint procedure batch / MEC ethics procedure | `kb_staging/complaint_procedure_ready.json` | `complaint_40_provider_misconduct` | inserted | exact-source-grounded ethics complaint steps, required fields, one-year deadline, one-working-day notification |
| Complaint procedure batch / HLIB non-ethics edge cases | `kb_staging/non_ethics_complaint_procedure_ready.json` | `complaint_29_inspection` | inserted | added exact service/admin complaint phrasings plus missing-contact fallback, anonymous/false complaint handling, fixable-error timing, forwarding, and three-day notice wording |
| Adult eligibility batch / exact-source answer alignment | `kb_staging/batch_3_adult_eligibility.json` | `eligibility_status_coverage_root_v1` | inserted | aligned root answer wording to exact staged facts about eligible groups and service-type dependence |

## Required fields for future registry entries

- source title
- source URL
- source type
- exact excerpt summary
- destination family/root/card
- inserted or held out
- reason
- validation result
- regression result
