# Pre-registration: the case study with the tests committed

Written 2026-09-26, **before any run**, committed with the harness change and
the run script.

## Why

In the case study (`README.md`), Claude Code with Haiku 4.5 solved 33/36 and
Sonnet 5 36/36. All three Haiku failures were the same behaviour: the task's
new tests sat in the workspace as uncommitted changes, and Haiku reverted them
with `git checkout`, `git restore` or `git stash`. Sonnet never did.

That is partly a model habit and partly a harness artifact: Groundhog always
delivered the tests uncommitted. This run separates the two by changing only
how the tests arrive.

## The one change

`groundhog run --commit-tests` (new in this commit): the task's tests are
committed on top of the parent (`Add failing tests`, author `groundhog`), so
they are part of `HEAD` and `git status` is clean at the start. Nothing else
about the workspace, the sandbox or the grading changes; patches and changed
files are still taken against the parent with the test files excluded.
Unit tests show `git checkout -- .`, `git restore` and `git stash`/`pop` leave
committed tests intact, and revert uncommitted ones.

## Arm

Haiku 4.5 only, `claude-code:haiku-4.5-committed`: the same Claude Code
2.1.276 command, flags, `--sandbox required`, timeouts, 36 tasks (hash
`efdaa0f35dcfc38f`) and clones (same HEADs as the case study) as the case
study's Haiku arm, plus `--commit-tests`. One attempt per task.

Sonnet 5 is not re-run: it touched no test file in 36 attempts and solved all
36, so committing the tests has nothing to change for it. Comparisons to
Sonnet below use the case study's Sonnet arm, and say so.

## Analysis

**Primary.** Attempts that modified a task test file: case-study Haiku 3/36
versus this arm. If the behaviour was mostly the harness, this falls to 0 or 1.
Reported as counts with the transcripts of any that remain.

**Secondary.**
1. Solves, paired against the case-study Haiku arm: exact McNemar. With one
   attempt per task, a few flips either way are run-to-run noise; significance
   needs at least 6 one-directional flips and is not expected.
2. Solves against the case-study Sonnet arm (36/36), same test, noting the
   conditions differ in how tests were delivered.
3. The `compare` behaviour table and API-equivalent cost from Claude Code's
   session logs, priced as in the case study.

## Stated in advance

- If test modifications drop to 0-1 and Haiku solves 35-36, the case study's
  gap was mostly the harness, and the case study README and the blog post say
  so plainly.
- If Haiku still reverts or edits tests with them committed, it is a model
  behaviour, and that is the finding.
- Anything in between is reported as it comes out.
- A harness error is re-run once; an agent timeout is a failure.
