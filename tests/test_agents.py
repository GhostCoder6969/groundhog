"""External agent adapter, and the guards that make it safe to trust."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groundhog import agents, validate  # noqa: E402


class TestRender:
    def test_fills_placeholders(self):
        out = agents.render("aider --message-file {prompt_file}", prompt_file="/tmp/p.md")
        assert "/tmp/p.md" in out

    def test_quotes_every_substitution(self):
        """Commit subjects reach a shell; nothing is interpolated unquoted."""
        out = agents.render("run {prompt}", prompt="hi; rm -rf /")
        assert "; rm -rf /" not in out.replace("'hi; rm -rf /'", "")
        assert out.startswith("run '")

    def test_leaves_unknown_placeholders_alone(self):
        assert "{mystery}" in agents.render("x {mystery}", prompt_file="p")


class TestPrompt:
    def test_names_the_tests_that_must_pass(self):
        task = {"fail_to_pass": ["tests/t.py::test_a"], "test_files": ["tests/t.py"]}
        prompt = agents.build_prompt(task, "AssertionError", "pytest -q")
        assert "tests/t.py::test_a" in prompt
        assert "AssertionError" in prompt
        assert "pytest -q" in prompt

    def test_forbids_editing_tests(self):
        prompt = agents.build_prompt({"test_files": ["tests/t.py"]}, "boom", "pytest")
        assert "Do not modify any test file" in prompt

    def test_falls_back_to_test_files(self):
        prompt = agents.build_prompt({"test_files": ["tests/t.py"]}, "boom", "pytest")
        assert "tests/t.py" in prompt


class TestExternalRun:
    def test_runs_in_the_worktree(self, tmp_path):
        result = agents.run_external(tmp_path, "pwd", "prompt", "pytest", timeout=30)
        assert result.exit_code == 0
        assert str(tmp_path.resolve()) in result.output

    def test_agent_can_read_the_prompt_file(self, tmp_path):
        result = agents.run_external(tmp_path, "cat {prompt_file}", "THE-TASK", "pytest", timeout=30)
        assert "THE-TASK" in result.output

    def test_cleans_up_the_prompt_file(self, tmp_path):
        agents.run_external(tmp_path, "true", "p", "pytest", timeout=30)
        assert not (tmp_path / ".groundhog-task.md").exists()

    def test_timeout_is_recorded_not_raised(self, tmp_path):
        result = agents.run_external(tmp_path, "sleep 5", "p", "pytest", timeout=1)
        assert result.timed_out and "timed out" in result.error

    def test_failure_exit_code_is_captured(self, tmp_path):
        assert agents.run_external(tmp_path, "exit 3", "p", "pytest", timeout=30).exit_code == 3

    def test_exports_env_for_agents_that_look_there(self, tmp_path):
        result = agents.run_external(tmp_path, "echo $GROUNDHOG_TEST_CMD", "p", "pytest -q", timeout=30)
        assert "pytest -q" in result.output


class TestPytestParsing:
    """FAIL_TO_PASS / PASS_TO_PASS depend entirely on reading pytest correctly."""

    SAMPLE = """
tests/test_a.py::test_one PASSED                                         [ 25%]
tests/test_a.py::test_two FAILED                                         [ 50%]
tests/test_b.py::test_three SKIPPED                                      [ 75%]
tests/test_b.py::test_four[param-1] PASSED                               [100%]
"""

    def test_reads_each_outcome(self):
        out = validate.test_outcomes(self.SAMPLE)
        assert out["tests/test_a.py::test_one"] == "PASSED"
        assert out["tests/test_a.py::test_two"] == "FAILED"

    def test_handles_parametrised_tests(self):
        assert "tests/test_b.py::test_four[param-1]" in validate.test_outcomes(self.SAMPLE)

    def test_passing_excludes_failures_and_skips(self):
        assert validate.passing(self.SAMPLE) == {
            "tests/test_a.py::test_one",
            "tests/test_b.py::test_four[param-1]",
        }

    def test_empty_output(self):
        assert validate.passing("") == set()


class TestIsolatedWorkspace:
    """An agent with a shell must not be able to read the fix out of git."""

    def _repo(self, tmp_path):
        import subprocess
        repo = tmp_path / "src"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True,
                                      capture_output=True, text=True).stdout.strip()
        g("init", "-q")
        g("config", "user.email", "t@t"); g("config", "user.name", "t")
        (repo / "lib.py").write_text("def f():\n    return 1\n")
        g("add", "."); g("commit", "-qm", "base")
        parent = g("rev-parse", "HEAD")
        (repo / "tests").mkdir()
        (repo / "tests/test_lib.py").write_text("from lib import f\n\ndef test_f():\n    assert f() == 2\n")
        (repo / "lib.py").write_text("def f():\n    return 2  # THE-FIX\n")
        g("add", "."); g("commit", "-qm", "fix f")
        sha = g("rev-parse", "HEAD")
        task = {"sha": sha, "parent": parent, "test_files": ["tests/test_lib.py"],
                "subject": "fix f", "language": "python"}
        return repo, task

    def test_later_commits_are_unreachable(self, tmp_path):
        from groundhog.run import Workspace
        repo, task = self._repo(tmp_path)
        ws = Workspace(repo, task, None, "python -m pytest {tests}", 30, isolated=True)
        try:
            result = agents.run_external(
                ws.tree, "git log --all --format=%H; git remote -v; "
                         "git grep THE-FIX $(git rev-list --all)",
                "p", "pytest", timeout=30)
            assert task["sha"] not in result.output
            assert "THE-FIX" not in result.output
            missing = agents.run_external(
                ws.tree, f"git cat-file -e {task['sha']}", "p", "pytest", timeout=30)
            assert missing.exit_code != 0
            # The parent keeps its real SHA, so the patch diff still works.
            assert validate.git(ws.tree, "rev-parse", "HEAD").strip() == task["parent"]
            assert (ws.tree / "tests/test_lib.py").is_file()
            assert "return 1" in (ws.tree / "lib.py").read_text()
        finally:
            ws.close()
        assert not ws.tmp.exists()

    def test_worktree_mode_is_unchanged_for_the_builtin_loop(self, tmp_path):
        from groundhog.run import Workspace
        repo, task = self._repo(tmp_path)
        ws = Workspace(repo, task, None, "python -m pytest {tests}", 30)
        try:
            assert (ws.tree / "tests/test_lib.py").is_file()
            assert validate.git(ws.tree, "rev-parse", "HEAD").strip() == task["parent"]
        finally:
            ws.close()

    def test_committed_tests_survive_git_tidying(self, tmp_path):
        # The case study's Haiku failures: git checkout/restore/stash on the
        # task's uncommitted tests threw them away. Committed, they survive.
        from groundhog.run import Workspace
        repo, task = self._repo(tmp_path)
        ws = Workspace(repo, task, None, "python -m pytest {tests}", 30, isolated=True, commit_tests=True)
        try:
            tidy = agents.run_external(
                ws.tree, "git checkout -- . && git restore tests && git stash && git stash pop; "
                         "git status --porcelain", "p", "pytest", timeout=30)
            assert "tests/" not in tidy.output
            assert ws.tests_were_modified() == []
            assert validate.git(ws.tree, "rev-parse", "HEAD~1").strip() == task["parent"]
            assert task["sha"] not in validate.git(ws.tree, "log", "--all", "--format=%H")
        finally:
            ws.close()

    def test_uncommitted_tests_are_lost_to_the_same_tidying(self, tmp_path):
        # The default, kept for comparability: the same commands revert them.
        from groundhog.run import Workspace
        repo, task = self._repo(tmp_path)
        ws = Workspace(repo, task, None, "python -m pytest {tests}", 30, isolated=True)
        try:
            agents.run_external(ws.tree, "git checkout -- . ; git clean -fdq tests",
                                "p", "pytest", timeout=30)
            assert ws.tests_were_modified() == ["tests/test_lib.py"]
        finally:
            ws.close()


def test_workspace_path_does_not_name_the_fix_commit(monkeypatch, tmp_path):
    # The task id is the fix commit; an agent with a shell can run pwd.
    from groundhog import run

    prefixes = []

    def mkdtemp(prefix=""):
        prefixes.append(prefix)
        raise RuntimeError("stop after naming")

    monkeypatch.setattr(run.tempfile, "mkdtemp", mkdtemp)
    task = {"sha": "b90faad1c0ffee", "parent": "a" * 40, "test_files": [], "source_files": []}
    with pytest.raises(RuntimeError):
        run.Workspace(tmp_path, task, None, "true", 10, isolated=True)
    assert prefixes and "b90faad1" not in prefixes[0]
