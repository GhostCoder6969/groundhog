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

Each of the ten patches was applied to a fresh worktree at the task's
parent commit, with the task's test files checked out from the fixing
commit, and the entire suite run with `python -m pytest tests/ -q`:

| task | subject | suite after the patch | failures outside the task |
|---|---|---|---:|
| afc2e0557ff7 | groundhog bench | 273 passed | 0 |
| 878751561ca2 | external agents are not unmeasured | 271 passed | 0 |
| 95d8b36f3959 | Rust detection and parser | 269 passed | 0 |
| c4e9c34f957a | validate --stability | 261 passed | 0 |
| 454839e6482a | --jobs | 258 passed | 0 |
| 17ee2e809a31 | pyproject without tomllib | 256 passed | 0 |
| 3ec44b8ca7e4 | --system-prompt, --sample | 254 passed | 0 |
| 3fd2cc81fc6a | groundhog doctor | 251 passed | 0 |
| b485405a0b7a | report --markdown, badge | 244 passed | 0 |
| a7ea847a53df | F2P-only overstatement section | 238 passed | 0 |

The passing counts fall because older parent commits have fewer tests.
No patch broke anything outside its own task, so the 10/10 holds under
full-suite PASS_TO_PASS, not only file scope. The check is the script in
the commit that added this file's parent section; it is what
`validate --p2p-scope full` does automatically, and the next dogfood run
should simply use that flag.
