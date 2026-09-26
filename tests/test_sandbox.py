"""Issue #57: an external agent must not be able to read the fix from disk."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groundhog import demo, sandbox  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
needs_sandbox = pytest.mark.skipif(sandbox.available() is None, reason="no sandbox-exec or bwrap here")

# Ignores the task. Finds the commit after its own HEAD in a copy of the
# history and applies that commit's source changes -- the attack from #57.
STEAL = ('P=$(git rev-parse HEAD); '
         'C=$(git -C {src} rev-list --all --children | awk -v p=$P \'$1==p {{print $2}}\'); '
         'git -C {src} diff $P $C -- demolib | git apply')


class TestBuild:
    def test_denies_the_answer_and_re_allows_the_venv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sandbox, "available", lambda: "sandbox-exec")
        repo, cache, ws = tmp_path / "repo", tmp_path / "cache", tmp_path / "ws"
        venv = cache / "repo-abc"
        tasks = tmp_path / "tasks.jsonl"
        for d in (repo, venv, ws):
            d.mkdir(parents=True)
        tasks.write_text("{}\n")
        box = sandbox.build("auto", repo=repo, cache=cache, workspace=ws, venv=venv, tasks=tasks)
        assert box.deny == [repo.resolve(), cache.resolve(), tasks.resolve()]
        assert box.allow == [venv.resolve()]
        profile = box.profile()
        assert f'(literal "{tasks.resolve()}")' in profile
        assert profile.index("deny") < profile.index("(allow file-read* file-write* (subpath")

    def test_never_denies_home_or_the_workspace(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sandbox, "available", lambda: "sandbox-exec")
        ws = tmp_path / "ws"
        ws.mkdir()
        box = sandbox.build("auto", repo=Path.home(), cache=tmp_path, workspace=ws, venv=None)
        assert box.deny == []

    def test_required_without_a_sandbox_refuses(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sandbox, "available", lambda: None)
        with pytest.raises(sandbox.SandboxUnavailable):
            sandbox.build("required", repo=tmp_path, cache=tmp_path, workspace=tmp_path, venv=None)
        assert sandbox.build("auto", repo=tmp_path, cache=tmp_path, workspace=tmp_path, venv=None).kind == "none"

    def test_bwrap_hides_dirs_under_tmpfs_and_files_under_dev_null(self, tmp_path):
        d, f = tmp_path / "d", tmp_path / "f"
        d.mkdir()
        f.write_text("x")
        argv = sandbox.Sandbox("bwrap", [d, f], [d / "venv"]).wrap("true")
        assert argv[:3] == ["bwrap", "--dev-bind", "/"]
        assert ["--tmpfs", str(d)] == argv[argv.index("--tmpfs"):argv.index("--tmpfs") + 2]
        assert ["--ro-bind", "/dev/null", str(f)] == argv[argv.index("--ro-bind"):argv.index("--ro-bind") + 3]
        assert argv[-3:] == ["/bin/sh", "-c", "true"]


@pytest.fixture(scope="module")
def mined(tmp_path_factory):
    """The demo repo with validated tasks, and a copy of it in the clone cache."""
    base = tmp_path_factory.mktemp("sbx")
    repo, cache = base / "demolib", base / "cache"
    demo.build_repo(repo)
    subprocess.run(["git", "clone", "-q", str(repo), str(cache / "repos" / "local" / "me" / "demolib")], check=True)
    env = dict(os.environ, GROUNDHOG_CACHE=str(cache))
    for args in (["mine", str(repo), "--since", "10 years ago", "--out", str(base / "cand.jsonl")],
                 ["validate", str(repo), "--candidates", str(base / "cand.jsonl"),
                  "--out", str(base / "tasks.jsonl")]):
        subprocess.run([sys.executable, "-m", "groundhog", *args], cwd=ROOT, env=env,
                       check=True, capture_output=True, timeout=600)
    return base, repo, cache, env


def race(mined, source: str, mode: str) -> list[dict]:
    base, repo, cache, env = mined
    out = base / f"{mode}-{abs(hash(source))}.jsonl"
    subprocess.run([sys.executable, "-m", "groundhog", "run", str(repo), "--tasks", str(base / "tasks.jsonl"),
                    "--out", str(out), "--models", "cheat", "--agent-cmd", STEAL.format(src=source),
                    "--sandbox", mode, "--limit", "3", "--timeout", "120"],
                   cwd=ROOT, env=env, check=True, capture_output=True, timeout=600)
    return [json.loads(line) for line in out.read_text().splitlines() if line.strip()]


@needs_sandbox
@pytest.mark.parametrize("where", ["source clone", "clone cache"])
def test_a_cheat_that_reads_history_on_disk_scores_zero(mined, where):
    _, repo, cache, _ = mined
    source = str(repo) if where == "source clone" else str(cache / "repos" / "local" / "me" / "demolib")
    unsandboxed = race(mined, source, "off")
    assert any(r["solved"] for r in unsandboxed), "the cheat must work without a sandbox, or this proves nothing"
    assert all(r["sandbox"] == "none" for r in unsandboxed)
    sandboxed = race(mined, source, "required")
    assert sandboxed and not any(r["solved"] for r in sandboxed), sandboxed
    assert all(r["sandbox"] == sandbox.available() for r in sandboxed)
