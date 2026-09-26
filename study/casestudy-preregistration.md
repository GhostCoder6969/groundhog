# Pre-registration: can we switch Claude Code to the cheaper model?

Written 2026-09-26, **before any of the runs below**, and committed with the
task files and the run script, so neither the tasks nor the analysis can have
been chosen after seeing results.

## Question

A team using Claude Code on its own code asks the everyday question: can we
switch from Sonnet 5 to Haiku 4.5? This is Groundhog's intended use, done once
in public on real repositories: hold the tasks and the agent fixed, change one
thing, and let a paired test say whether the difference is real, with the
behaviour behind it.

## Arms

Identical except for `--model`:

| arm | label | model |
|---|---|---|
| A (before) | `claude-code:sonnet-5` | `claude-sonnet-5` |
| B (after) | `claude-code:haiku-4.5` | `claude-haiku-4-5-20251001` |

Both: Claude Code 2.1.276, headless,
`claude -p {prompt} --permission-mode bypassPermissions --disallowedTools WebFetch WebSearch`,
in a clean environment (`env -i HOME PATH USER TERM`), exactly as in the
frontier run except for the model and the sandbox.

**Sandboxed.** Every attempt runs with `--sandbox required` (sandbox-exec on
this Mac), so the agent cannot read the source clone, the clone cache, the
task file or earlier patches (issue #57). The frontier run predates this; one
of its attempts read the fix from the clone. An attempt that records any
sandbox other than `sandbox-exec` is invalid and is re-run.

## Tasks (36, fixed now)

The frontier run's 36 tasks, unchanged, copied to `study/casestudy/tasks-*.jsonl`:
click 8, httpx 8, werkzeug 4, attrs 4, jinja 4, marshmallow 4, rich 4.
Task-set hash `efdaa0f35dcfc38f` (sha256 of the sorted fix SHAs).

Re-validated today against fresh clones with the current harness (after the
#56 environment fix): 36 of 36 still fail without the fix and pass with it.
Clone HEADs at registration:

| repo | upstream | HEAD |
|---|---|---|
| click | pallets/click | `06b2a6787411` |
| httpx | encode/httpx | `b5addb64f016` |
| werkzeug | pallets/werkzeug | `671537e0e5c7` |
| attrs | python-attrs/attrs | `8f767776326f` |
| jinja | pallets/jinja | `5ef70112a1ff` |
| marshmallow | marshmallow-code/marshmallow | `7f0792bd7a06` |
| rich | Textualize/rich | `9d8f9a372cc5` |

Harness: Groundhog at `7d585627fe7a`.

## Procedure

- One attempt per task per arm (72 attempts), `--agent-timeout 900`, test `--timeout 300`.
- Per repository, both arms run back to back, and which arm goes first
  alternates by repository, so neither arm systematically gets a quieter
  machine or a later hour.
- Scoring is Groundhog's usual rule: target tests pass, no previously passing
  test in the task's test files breaks, no test file edited.
- An attempt that fails for a harness reason (not the agent: e.g. environment
  build) is re-run once and the re-run counts. Agent timeouts count as failures.

## Primary analysis

`groundhog compare` on the 36 paired tasks, A vs B: exact two-sided McNemar
test at alpha = 0.05.

The frontier run solved 35/36 with Sonnet (unsandboxed), so arm A is expected
near the ceiling. Significance then needs at least 6 discordant tasks, nearly
all in one direction. With fewer, the result is reported as "no detectable
difference on 36 tasks", not as "no difference", with the confidence intervals.

## Secondary, descriptive

From the same `compare` output, per arm: target-tests-only rate against true
rate (the FAIL_TO_PASS-only overstatement), attempts that broke passing tests,
attempts that edited a test, harness errors, median wall time and median
files touched. Plus every flipped task with the losing side's reason, and the
patches for each. Cost is not reported: Groundhog does not yet read Claude
Code's own cost, and these runs use a subscription.

The Sonnet arm is also a sandboxed replication of the frontier run; its
agreement with that run's 35/36 is reported, task by task.

## What will be published

Whatever comes out: `study/casestudy/README.md` with the compare output, the
results files, every patch, and the logs. If the result is null, it is
reported as null.
