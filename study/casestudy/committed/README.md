# Variant: the case study with the tests committed

Pre-registered in [`../committed-tests-preregistration.md`](../committed-tests-preregistration.md)
(commit `bc207f4`) before any run. Run 2026-09-26, 22:59–23:38 UTC.

The case study's Haiku 4.5 arm again, identical except for `--commit-tests`:
the task's tests arrive as a commit on top of the parent instead of as
uncommitted changes. All 36 attempts recorded `sandbox-exec` and
`tests_committed`. No harness errors, no re-runs.

## Result

| | Haiku, tests uncommitted (case study) | Haiku, tests committed | Sonnet 5 (case study) |
|---|---:|---:|---:|
| Solved | 33/36 | **34/36** | 36/36 |
| Target tests passed (F2P-only) | 35/36 | 35/36 | 36/36 |
| **Edited a test** | **3** | **0** | 0 |
| Broke passing tests | 1 | 2 | 0 |
| Agent timeouts | 0 | 1 | 0 |
| Median / p90 time | 77s / 183s | 77s / 176s | 69s / 204s |
| API-equivalent cost, total | $8.22 | $7.49 | $10.34 |
| Cost per solved task | $0.25 | $0.22 | $0.29 |

**Primary (test modifications):** 3/36 → **0/36**. With the tests committed,
Haiku never reverted or edited them. The behaviour in the case study was the
harness handing it uncommitted tests.

**Secondary 1, solves vs the uncommitted Haiku arm:** 33 → 34, one task
flipped (click pager, now solved). McNemar p = 1.0. As pre-registered, a single
flip is run-to-run noise territory. Output: [`committed-vs-haiku.txt`](committed-vs-haiku.txt).

**Secondary 2, vs Sonnet 5:** 34 vs 36, two flips, both Sonnet-only, p = 0.5.
No detectable difference on 36 tasks. Output: [`committed-vs-sonnet.txt`](committed-vs-sonnet.txt).

## Against what was stated in advance

The pre-registration said: 0–1 test modifications *and* 35–36 solves would
mean the case study's gap was mostly the harness. The result is in between,
and splits cleanly:

- **The test reverting was entirely the harness.** 3 → 0.
- **Two of the three failures were real, and did not go away.** On the same
  two tasks, Haiku failed again for different reasons:

| task | tests uncommitted | tests committed |
|---|---|---|
| attrs: Expose converter as a decorator | reverted the tests with `git checkout` | target tests passed, **broke 2 other tests** |
| jinja: trio / missing aclose | reverted the tests, target failed, broke 29 | **timed out** at 900s, target failed, broke 13 |
| click: close the pager temp file | reverted the tests with `git restore` | **solved** |

The attrs attempt is the failure this project was built to catch: the target
tests pass, so a FAIL_TO_PASS-only harness scores it solved, and two previously
passing tests are broken. Haiku's F2P-only score is 35/36 in both arms.

## Cost

Priced as in the case study, from Claude Code's session logs at API list rates
(Haiku 4.5 $1 / $5 per million input / output tokens, cache writes 1.25×,
cache reads 0.1×). The committed arm cost $7.49, 28% less than Sonnet's $10.34;
per solved task, $0.22 against $0.29.

## What this changes

- The case study's headline mechanism ("Haiku reverts uncommitted tests") is a
  harness interaction, not a model property to warn people about. The case
  study README says so.
- Handing agents uncommitted tests is ordinary TDD, but it is not what most
  teams' agents see, so Groundhog should probably default to committing them.
  That changes every task's workspace, so it is a separate, deliberate
  decision; this run only adds the option.

## Files

- `haiku-4.5-committed-<repo>.jsonl`, `../haiku-4.5-committed.jsonl`: the records.
- `patches/`: every attempt's diff beside the human fix.
- `logs/`: `groundhog run` output per repository.
- `committed-vs-haiku.*`, `committed-vs-sonnet.*`: the pre-registered comparisons.
- `../../../scripts/casestudy_committed_run.sh`: the exact run.

## Deviations

None in procedure. After the run, the `compare` flip list was fixed to name a
timeout as "timed out" and to stop saying "target passed" when it had not
(the jinja attempt). That changes a label, not a count; the case study's own
comparison output is byte-identical after the fix.
