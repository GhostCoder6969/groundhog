#!/usr/bin/env bash
# The case study pre-registered in study/casestudy-preregistration.md:
# Claude Code on Sonnet 5 vs Haiku 4.5, same 36 tasks, sandboxed.
# Per repository both arms run back to back; which goes first alternates.
# --resume makes a re-run pick up where an interrupted one stopped.
set -uo pipefail
REPOS_DIR="${REPOS_DIR:?set REPOS_DIR to the directory holding the clones}"
OUT=study/casestudy/results
mkdir -p "$OUT" study/casestudy/logs

agent() {
  echo "env -i HOME=\"\$HOME\" PATH=\"\$PATH\" USER=\"\$USER\" TERM=dumb claude -p {prompt} --permission-mode bypassPermissions --model $1 --disallowedTools WebFetch WebSearch"
}

arm() {  # arm <label> <model id> <repo>
  python3 -m groundhog run "$REPOS_DIR/$3" \
      --models "claude-code:$1" --agent-cmd "$(agent "$2")" \
      --tasks "study/casestudy/tasks-$3.jsonl" \
      --out "$OUT/$1-$3.jsonl" \
      --sandbox required --timeout 300 --agent-timeout 900 --resume \
      >> "study/casestudy/logs/$1-$3.log" 2>&1
  echo "done $1 $3 $(date -u '+%H:%M:%S')"
}

repo() {  # repo <name> <0|1>: 0 runs Sonnet first, 1 runs Haiku first
  if [ "$2" = 0 ]; then
    arm sonnet-5 claude-sonnet-5 "$1"; arm haiku-4.5 claude-haiku-4-5-20251001 "$1"
  else
    arm haiku-4.5 claude-haiku-4-5-20251001 "$1"; arm sonnet-5 claude-sonnet-5 "$1"
  fi
}

# Three lanes, each owning its repositories, so no two workers build the same venv.
( repo click 0; repo werkzeug 1; repo attrs 0 ) &
( repo httpx 1; repo marshmallow 0 ) &
( repo jinja 0; repo rich 1 ) &
wait
echo "ALL DONE $(date -u '+%H:%M:%S')"
