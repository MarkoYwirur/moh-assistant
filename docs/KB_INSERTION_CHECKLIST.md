# KB Insertion Checklist

Use this checklist for every narrow content batch.

1. Confirm the architecture is frozen and the target family is already live.
2. Prefer an existing live root/card over a new live card.
3. Insert only source-grounded facts.
4. Add only exact or high-value citizen phrasings.
5. Keep narrow facts narrow.
6. Do not generalize beyond the excerpt.
7. Run:

```powershell
py run_validate_kb_utf8.py
py run_regression.py
```

8. Run targeted phrase checks for the inserted facts.
9. If regression fails, revert the content batch.
10. Record in the source registry:
   - source
   - destination
   - inserted phrases
   - held-out facts
   - validation/regression result
