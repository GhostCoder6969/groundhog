"""Keep an external agent away from the answer on disk (issue #57).

The isolated checkout leaves no future commit in the agent's own workspace,
but the full history is still on disk: the source clone Groundhog was pointed
at, the clone cache under ~/.cache/groundhog/repos, the task file (which names
the fix commit), and earlier attempts' patches. An agent with a shell runs as
the same user and can read all of it; one frontier attempt did, with `find /`.

So external agents run under the OS sandbox with those paths unreadable:
sandbox-exec on macOS, bubblewrap on Linux. Everything else stays as it was --
the agent still needs its own config, the network for its API, the toolchain
and the venv -- which is why this is a deny list rather than an allow list.

What it cannot cover: another copy of the repository the harness does not know
about, and the public repository on the network. `--sandbox-deny` adds paths.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("auto", "required", "off")


class SandboxUnavailable(RuntimeError):
    pass


def available() -> str | None:
    """The sandbox this machine can apply, or None."""
    if sys.platform == "darwin" and shutil.which("sandbox-exec"):
        return "sandbox-exec"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bwrap"
    return None


@dataclass
class Sandbox:
    kind: str                                         # "sandbox-exec", "bwrap" or "none"
    deny: list[Path] = field(default_factory=list)    # unreadable to the agent
    allow: list[Path] = field(default_factory=list)   # readable even inside a denied path

    def wrap(self, command: str) -> list[str] | str:
        """The agent command as argv under the sandbox, or unchanged for "none"."""
        if self.kind == "sandbox-exec":
            return ["sandbox-exec", "-p", self.profile(), "/bin/sh", "-c", command]
        if self.kind == "bwrap":
            argv = ["bwrap", "--dev-bind", "/", "/", "--die-with-parent"]
            for path in self.deny:
                # A directory is hidden under an empty tmpfs, a file under /dev/null.
                argv += ["--tmpfs", str(path)] if path.is_dir() else ["--ro-bind", "/dev/null", str(path)]
            for path in self.allow:
                argv += ["--bind", str(path), str(path)]
            return [*argv, "/bin/sh", "-c", command]
        return command

    def profile(self) -> str:
        """SBPL for sandbox-exec. Later rules win, so allows follow denies."""
        lines = ["(version 1)", "(allow default)"]
        for path in self.deny:
            lines.append(f"(deny file-read* file-write* ({_filter(path)} {_quote(path)}))")
        for path in self.allow:
            lines.append(f"(allow file-read* file-write* (subpath {_quote(path)}))")
        return "\n".join(lines)


def build(mode: str, *, repo: Path, cache: Path, workspace: Path, venv: Path | None,
          tasks: Path | None = None, results: Path | None = None,
          patches: Path | None = None, extra: list[Path] | None = None) -> Sandbox:
    """The sandbox for one external-agent attempt.

    `required` raises when no sandbox is available; `auto` falls back to none,
    and the attempt records that it ran unsandboxed.
    """
    if mode not in MODES:
        raise ValueError(f"sandbox mode must be one of {', '.join(MODES)}")
    kind = available() if mode != "off" else None
    if kind is None:
        if mode == "required":
            raise SandboxUnavailable(
                "--sandbox required, but neither sandbox-exec (macOS) nor bwrap (Linux) "
                "is available. Install bubblewrap, or pass --sandbox auto to run unsandboxed.")
        return Sandbox("none")

    # Never hide the workspace or home, or a folder containing either: that
    # would break the agent, not protect the answer. The venv lives inside the
    # cache, so it is re-allowed below instead.
    keep = [workspace.resolve(), Path.home().resolve()]
    deny: list[Path] = []
    for path in (repo, cache, tasks, results, patches, *(extra or [])):
        if path is None or not path.exists():
            continue
        path = path.resolve()
        if any(path == k or path in k.parents for k in keep) or path in deny:
            continue
        deny.append(path)
    allow = []
    if venv is not None and any(venv.resolve().is_relative_to(d) for d in deny):
        allow.append(venv.resolve())
    return Sandbox(kind, deny, allow)


def _filter(path: Path) -> str:
    return "subpath" if path.is_dir() else "literal"


def _quote(path: Path) -> str:
    return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'


__all__ = ["MODES", "Sandbox", "SandboxUnavailable", "available", "build"]
