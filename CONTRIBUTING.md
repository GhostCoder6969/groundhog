# Contributing to Groundhog

Groundhog is small on purpose: about 1,800 lines, no runtime dependencies, and
four files that each do one thing. You should be able to read the whole thing in
an afternoon and change it with confidence.

## How it fits together

```
mine.py      git log  ->  candidate commits        (pure git, fast, no execution)
validate.py  candidates -> real tasks              (runs the tests twice)
run.py       tasks    ->  attempts                 (agent loop in a worktree)
report.py    attempts ->  table + leaderboard page
models.py    provider-agnostic chat with tools
```

Data moves between stages as JSONL files, so every stage is independently
runnable and independently testable. If you are changing one stage you can ignore
the others.

**The one invariant that matters:** a task is only real if the tests fail without
the original fix and pass with it. Everything else is convenience. If a change
makes that check weaker, it will not be merged, however useful it seems.

## Setup

```bash
git clone https://github.com/abhinavsv3/groundhog
cd groundhog
pip install -e . pytest
python -m pytest tests/ -q
```

The tests build throwaway git repositories on the fly, so there is nothing to
download and nothing to mock. They should run in under ten seconds.

## Ways in, roughly by difficulty

**Add a model provider** (easy). Anything OpenAI-compatible is one line in
the `HOSTS` table in `models.py`: name, base URL, key variable. Anthropic is
the worked example of a genuinely different wire format, if you need one.

**Add a language** (medium, most wanted). Python, Go, JavaScript and Rust
are supported; Java, Ruby and C# have issues open (52 to 54). A language is
three things: detection in `environment.py`, a per-test outcome parser in
`validate.py`, and how test files map to runner targets. Rust (commit
95d8b36) is the smallest worked example, and its issue (31) still needs
someone with cargo to validate a real crate.

**Read an external agent's cost** (medium, issue 47). Claude Code and Codex
print tokens and dollars in their structured output; the COST column is
empty for every `--agent` run because nobody parses it yet.

**Extend environment inference** (hard, high impact). `environment.py` handles
Python projects — extras, PEP 735 dependency groups, `requirements*.txt` — and
caches a venv per repo. It does not handle native extensions, service
dependencies or unusual build systems, which still need `--venv` and
`--test-cmd`. Two traps worth knowing: dependency groups are *not* extras
(`pip install '.[tests]'` exits 0 having installed nothing), and the venv cache
key must include the install plan or your improvement silently won't apply.

## Ten-minute contributions

Three things need no design discussion and help the most:

- **Verify an agent preset.** `groundhog run --list-agents` shows which are
  marked verified. Each unverified one has an issue with the four commands to
  run (issues 39 to 45). A pasted result record and a one-line PR flipping
  `verified=True` is the whole contribution.
- **Post a bench result.** Run `groundhog bench` on any repo and paste
  `report.md` in the
  [Show and tell discussion](https://github.com/abhinavsv3/groundhog/discussions/55).
  Private repos are welcome unnamed. Surprising collateral columns are the
  most useful thing anyone can send.
- **Run the demo on Windows** and say what breaks (issue 51). The CLI is
  known to run there; the test suite has eight Windows-specific failures
  nobody has looked at.

Issue templates exist for bugs, features, preset verification and new
languages; they ask for `groundhog doctor` output and the exact command, which
answers most questions before anyone has to ask them.

## What makes a good pull request

- **A test.** Especially for mining and validation heuristics: add a commit shape
  to the synthetic repo in `tests/test_pipeline.py` and assert what should happen
  to it.
- **Evidence it works on a real repo.** "Mined 40 tasks from X, 12 validated" is
  worth more than any description.
- **No new runtime dependencies** unless there is genuinely no alternative. Every
  dependency is another way a benchmark run dies on somebody's laptop.
- **Honesty about limits.** If your change works for pytest but not unittest, say
  so in the docstring. Silent partial correctness is how benchmarks start lying.

## Things that will get a change rejected

- Weakening the fail-to-pass check
- Scoring anything other than the test suite (no judge models, no partial credit)
- Letting the model edit test files
- Reporting a number without saying how it was produced

## A bug worth knowing about before you start

Editable installs shadow the worktree. If a repo uses a `src/` layout and the
package is installed with `pip install -e .` from the original clone, then
`import yourpackage` resolves to the *original, fixed* code no matter what the
model wrote — every test passes and every task looks like a harmless refactor.

`source_roots()` forces the worktree onto `PYTHONPATH` to prevent this. It cost
us 20 tasks on `pallets/click` before we noticed, and it failed *silently*. If
you are adding a language, assume the same class of bug exists there and go
looking for it.
