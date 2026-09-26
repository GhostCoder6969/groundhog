# Case study: can we switch Claude Code to the cheaper model?

Pre-registered in [`../casestudy-preregistration.md`](../casestudy-preregistration.md)
(commit `232ec9d`) before any run. Run 2026-09-26, 21:54–22:48 UTC.

Claude Code 2.1.276, headless, identical flags in both arms except `--model`.
Every attempt ran under `--sandbox required` (all 72 recorded `sandbox-exec`).
36 tasks from seven upstream repositories, one attempt per task per arm.

## Result

| | Sonnet 5 | Haiku 4.5 |
|---|---:|---:|
| Solved | **36/36** | **33/36** |
| 95% CI (Wilson) | 90% – 100% | 78% – 97% |
| Target tests passed (F2P-only) | 36/36 | 35/36 |
| Broke passing tests | 0 | 1 |
| Edited a test | 0 | 3 |
| Harness errors | 0 | 0 |
| Median time per task | 69s | 77s |
| p90 / max time | 204s / 640s | 183s / 525s |
| API-equivalent cost, total | $10.34 | $8.22 |
| API-equivalent cost, median task | $0.19 | $0.12 |

**Primary analysis, as pre-registered:** exact McNemar on the 36 pairs.
Solved by Sonnet only: 3. By Haiku only: 0. By both: 33. **p = 0.25: no
detectable difference on 36 tasks.** Three discordant tasks cannot reach
significance even when all go one way (the floor is `2 × 0.5³`); the
pre-registration said at least 6 were needed. This is "we do not know from
36 tasks", not "no difference". Full output: [`compare.txt`](compare.txt),
[`compare.json`](compare.json).

## What the three flips were

All three Haiku failures were the same behaviour, and Sonnet did it zero times
in 36 attempts. The task's new tests are delivered in the workspace as
uncommitted changes on top of the parent commit. Haiku ran `git diff` or
`git status`, took them for stray edits, and reverted them:

| task | repo | what Haiku did (from its Claude Code transcript) | graded |
|---|---|---|---|
| Expose converter as a decorator (#1541) | attrs | `git checkout tests/test_make.py`, then hand-edited two tests back in and changed a helper in `tests/strategies.py` | edited a test |
| Close the pager temp file before unlinking it | click | `git restore tests/test_termui.py`, `git checkout HEAD -- tests/test_termui.py`, then re-added parts by hand | edited a test |
| test on trio, fix all missing aclose | jinja | `git stash` / `git stash pop` around test runs, then `git checkout tests/test_async.py tests/test_async_filters.py` | edited a test; target tests failed; 29 previously passing tests broke |

In two of the three, the source fix itself passed the target tests: Haiku's
F2P-only score is 35/36. A harness that did not check test files would have
reported Haiku within one task of Sonnet.

**How much of this is the harness?** Real, and partly an artifact. Real:
handing an agent uncommitted failing tests is ordinary TDD practice, and one
model discarded them where the other never did. Artifact: in these tasks the
tests are *always* uncommitted, which makes the behaviour far more likely than
in a repository where the tests arrive as a commit. A variant that commits the
task's tests into the workspace would separate the two; it is not part of this
pre-registered run.

**Answered by the pre-registered variant** ([`committed/`](committed/README.md)):
with the tests committed, Haiku edited a test **0** times in 36 attempts (3
here) and solved 34/36. The reverting was the harness. The attrs and jinja
tasks still failed, for real reasons this time: attrs passed its target tests
and broke 2 others, and jinja timed out. The click task was solved.

## Cost

Groundhog does not read Claude Code's spend yet. These figures come from the
token counts in Claude Code's own session logs (`~/.claude/projects/`), priced at
API list rates: Sonnet 5 $2 / $10 per million input / output tokens, Haiku 4.5
$1 / $5, cache writes at 1.25× input, cache reads at 0.1× input. Both arms ran
on a subscription, so the marginal cost here was plan usage, not dollars.

Haiku is half Sonnet's price per token, but the Haiku arm cost only **20% less**
in total. The median task was 34% cheaper, the mean only 21%: Haiku's
sessions have a long, expensive tail, so it spent more tokens than Sonnet to
get through the same tasks. Cost per *solved* task: Sonnet $0.29,
Haiku $0.25.

## Replication of the frontier run

The same 36 tasks ran with Sonnet 5 earlier the same day, unsandboxed
(`study/frontier-preregistration.md`), scoring 35/36, with one attempt known
to have read the fix from the source clone. Sandboxed, Sonnet 5 scored 36/36.
The two runs disagree on one task, jinja `1655128cfc0e` (the trio task):
unsandboxed Sonnet failed it, sandboxed Sonnet solved it. It is also the task
Haiku failed hardest. The contaminated attrs task was solved in both runs.
One attempt per task, so a single-task disagreement is within run-to-run noise.

## Files

- `tasks-*.jsonl`: the 36 tasks, unchanged from the frontier run.
- `results/<arm>-<repo>.jsonl`: one record per attempt; `sonnet-5.jsonl` and
  `haiku-4.5.jsonl` concatenate them per arm.
- `results/patches/`: every attempt's diff beside the human fix (`.human.diff`).
- `logs/`: the `groundhog run` output per arm and repository.
- `compare.txt`, `compare.json`: the pre-registered analysis.
- `../../scripts/casestudy_run.sh`: the exact run.

## Deviations from the pre-registration

None in procedure. No attempt needed a re-run: all 72 were sandboxed and none
hit a harness error. One analysis-tool fix was made after the run and before
this write-up: `compare` counted a test edit as a harness error too (the edit
is recorded in the same `error` field). That changed a descriptive row from
8% to 0%, not the primary analysis.
