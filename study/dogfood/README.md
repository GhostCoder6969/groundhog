# Groundhog on Groundhog

The first real run through `groundhog bench`, on this repository's own
history, 2026-09-26.

```bash
groundhog bench . --agent claude-code --limit 10 --since "2 weeks ago"
```

- `tasks.jsonl`, `tasks.manifest.json`: 22 tasks validated from 25
  candidates, `--stability 2`, file-scope PASS_TO_PASS. Pin this set to
  compare against.
- `results-claude-code.jsonl`: ten attempts, the newest ten tasks.
- `patches/`: each attempt's diff beside the human's fix (`.human.diff`).
- `report-claude-code.md`: the Markdown report.
- `badge-claude-code.json`: the shields.io endpoint file.

| Model | Solved | Pass rate | 95% CI | F2P-only | Collateral | Median |
|---|---:|---:|---|---:|---|---:|
| claude-code | 10/10 | 100% | 72% – 100% | 10/10 | 0 | 222s |

## Caveats, in order of importance

1. **Ten tasks.** The interval is 72% to 100%. This says the pipeline works
   end to end on a real repository with a real agent; it does not rank
   anything.
2. **Easiest possible target.** A small stdlib codebase whose tests specify
   each feature completely. The tasks were written by Claude in the two
   weeks before this run, so the agent is reproducing work its own model
   family did, with the tests as a complete spec.
3. **File-scope PASS_TO_PASS.** Several tasks add a brand-new test file, so
   their PASS_TO_PASS set is empty and "solved" means only that the new
   tests pass. To close that gap, every patch was re-applied at its parent
   commit and the entire suite run over it. See "Whole-suite check" below.
4. **No cost column.** Claude Code's spend is not read back yet
   ([issue 47](https://github.com/abhinavsv3/groundhog/issues/47)).

## Whole-suite check

Pending: the check was running when this file was written and its result
is appended below when it lands.
