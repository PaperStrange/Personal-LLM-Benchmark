# Examples

## Run the T0 gate on a sample candidate

```bash
python3 src/llm_workflow_eval/judge/t0_checks.py --task T1 \
  --candidate examples/t1-sample-candidate.md \
  --inventory fixture/DEBT-INVENTORY.md \
  --workdir fixture/legacy-billing
```

## Run the pack's own test suite

```bash
python3 tests/run_all.py
```
