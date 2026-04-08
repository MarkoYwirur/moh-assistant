# Anti-Overlap Rules

Do not reintroduce migration debt.

## Do

- prefer existing live roots
- add exact source-grounded phrasings
- keep narrow facts narrow
- hold out uncertain items for review
- verify with validation, regression, and targeted phrase checks

## Do not

- create a new live card when an existing live root can hold the fact
- add broad generic patterns “just in case”
- reopen completed migration families for content that can live inside the existing root
- touch `router.py`, `validate_kb.py`, or runtime flags during routine content ingestion
- promote shadow/helper artifacts into runtime truth

## When to hold content out

Hold it out if:

- the fact is too narrow and would widen a frozen family awkwardly
- the fact belongs to a specialist subflow that needs a dedicated pass
- the excerpt is real but the safe destination is unclear
