# Repo Operational Notes

## Frozen architecture

Do not casually touch:

- `router.py`
- `validate_kb.py`
- runtime flags
- completed migrated family structure

## Canonical workflow files

- demo pack: [demo/demo_phrase_pack.json](/c:/Users/Asus/Desktop/moh-assistant/demo/demo_phrase_pack.json)
- demo helper: [scripts/run_demo_pack.py](/c:/Users/Asus/Desktop/moh-assistant/scripts/run_demo_pack.py)
- demo runbook: [DEMO_RUNBOOK.md](/c:/Users/Asus/Desktop/moh-assistant/docs/DEMO_RUNBOOK.md)
- intake template: [KB_INTAKE_TEMPLATE.md](/c:/Users/Asus/Desktop/moh-assistant/docs/KB_INTAKE_TEMPLATE.md)
- insertion checklist: [KB_INSERTION_CHECKLIST.md](/c:/Users/Asus/Desktop/moh-assistant/docs/KB_INSERTION_CHECKLIST.md)
- source registry: [SOURCE_REGISTRY.md](/c:/Users/Asus/Desktop/moh-assistant/docs/SOURCE_REGISTRY.md)

## Historical scripts

The repo root contains many historical migration helpers such as:

- `fix_*`
- `patch_*`
- `step*`
- `run_*shadow.py`
- `router.py*.bak`
- `kb_step1_backup/`
- `kb_step1b_backup/`
- `kb/cards_backup.txt`

Treat them as historical or analysis tools unless the current task explicitly needs them.

## Windows note

When Armenian output matters, prefer:

```powershell
py -X utf8 scripts/run_demo_pack.py
```

The UTF-8 flag avoids misleading console corruption on Windows.

The same rule applies when reading docs or JSON in PowerShell. If `Get-Content` looks garbled, prefer:

```powershell
py -X utf8 -c "from pathlib import Path; print(Path('docs/DEMO_RUNBOOK.md').read_text(encoding='utf-8'))"
```

## Normal working set

For routine KB work, default to:

- `docs/DEMO_RUNBOOK.md`
- `docs/KB_INTAKE_TEMPLATE.md`
- `docs/KB_INSERTION_CHECKLIST.md`
- `docs/DESTINATION_MAP.md`
- `docs/SOURCE_REGISTRY.md`
- `docs/NEXT_SOURCE_BACKLOG.md`
- `scripts/run_demo_pack.py`

## Current known demo-risk

- generic phrase `այս դեղը ծածկվո՞ւմ է`
  - now safe with explanation, but still not the strongest demo anchor
  - prefer a concrete medicine query when possible
- generic phrase `երեխայի համար դեղ է ծածկվում`
  - safe with explanation
  - expect the system to ask for exact medicine name, dosage, and form
