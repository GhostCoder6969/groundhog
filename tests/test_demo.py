"""The demo is the project's main claim, executable. It must not rot."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groundhog import demo  # noqa: E402


class TestDemoRepo:
    @pytest.fixture(scope="class")
    def repo(self, tmp_path_factory):
        root = tmp_path_factory.mktemp("demo") / "demolib"
        demo.build_repo(root)
        return root

    def log(self, repo):
        return subprocess.run(["git", "-C", str(repo), "log", "--format=%s"],
                              capture_output=True, text=True).stdout

    def test_has_feature_commits(self, repo):
        subjects = self.log(repo)
        for name, *_ in demo.FEATURES:
            assert f"Add {name}()" in subjects

    def test_includes_a_refactor_for_validation_to_reject(self, repo):
        assert "Tidy clamp internals" in self.log(repo)

    def test_has_a_second_module_so_cross_module_damage_is_possible(self, repo):
        assert (repo / "demolib" / "numbers.py").exists()
        assert (repo / "tests" / "test_numbers.py").exists()

    def test_declares_its_own_dependencies(self, repo):
        """The demo claims zero-config setup; that needs a real manifest."""
        assert "dependency-groups" in (repo / "pyproject.toml").read_text()


class TestAgents:
    def test_one_honest_agent_and_several_cheats(self):
        names = [name for name, *_ in demo.AGENTS]
        assert "honest" in names
        assert {"saboteur", "test-editor", "idle"} <= set(names)

    def test_every_agent_command_is_templated_safely(self):
        for name, _, _, template in demo.AGENTS:
            rendered = template.format(fix="cp /fixes/a.py src/a.py", test="tests/t.py")
            assert "{" not in rendered, f"{name} left an unfilled placeholder"

    def test_saboteur_touches_another_module_not_the_test(self):
        _, _, _, template = next(a for a in demo.AGENTS if a[0] == "saboteur")
        rendered = template.format(fix="cp /fixes/a.py src/a.py", test="tests/t.py")
        assert "numbers.py" in rendered and "tests/t.py" not in rendered.split("&&")[1]

    def test_test_editor_touches_the_test(self):
        _, _, _, template = next(a for a in demo.AGENTS if a[0] == "test-editor")
        assert "{test}" in template

    def test_no_agent_reads_git_history(self):
        # The harness hides future commits from agents; a template that fetches
        # the fix with git would silently score 0 for every agent.
        for name, _, _, template in demo.AGENTS:
            assert "git" not in template, f"{name} reads history"

    def test_stage_fix_copies_the_fixed_source(self, tmp_path):
        repo = tmp_path / "demolib"
        demo.build_repo(repo)
        sha = subprocess.run(["git", "-C", str(repo), "log", "--format=%H", "--grep=Add dedupe"],
                             capture_output=True, text=True).stdout.strip()
        command = demo.stage_fix(repo, {"sha": sha, "source_files": ["demolib/text.py"]},
                                 tmp_path / "fixes")
        assert command.startswith("cp ") and command.endswith(" demolib/text.py")
        assert "def dedupe" in (tmp_path / "fixes" / "demolib" / "text.py").read_text()


class TestDemoEndToEnd:
    """Runs the whole demo. The honest agent must win and every cheat must lose."""

    def test_only_the_honest_agent_scores(self, tmp_path):
        done = subprocess.run([sys.executable, "-m", "groundhog", "demo", "--keep", str(tmp_path)],
                              capture_output=True, text=True, timeout=600,
                              cwd=Path(__file__).resolve().parents[1])
        assert done.returncode == 0, done.stdout + done.stderr
        records = [json.loads(line) for line in
                   (tmp_path / "out" / "results.jsonl").read_text().splitlines() if line.strip()]
        solved = {}
        for r in records:
            solved.setdefault(r["model"], []).append(r["solved"])
        assert solved["honest"] and all(solved["honest"]), solved
        for cheat in ("saboteur", "test-editor", "idle"):
            assert solved[cheat] and not any(solved[cheat]), (cheat, solved)


class TestShorten:
    def test_replaces_the_workspace_path(self, tmp_path):
        assert demo.shorten(f"{tmp_path}/out/x.jsonl", tmp_path) == "$DEMO/out/x.jsonl"

    def test_abbreviates_the_interpreter(self, tmp_path):
        assert demo.shorten(sys.executable, tmp_path) == "python"

    def test_leaves_ordinary_arguments_alone(self, tmp_path):
        assert demo.shorten("--limit", tmp_path) == "--limit"
