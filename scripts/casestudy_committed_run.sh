#!/usr/bin/env bash
# The committed-tests variant pre-registered in
# study/casestudy/committed-tests-preregistration.md: the case study's Haiku
# arm again, with the task's tests committed into the workspace.
set -uo pipefail
REPOS_DIR="${REPOS_DIR:?set REPOS_DIR to the directory holding the clones}"
OUT=study/casestudy/committed
mkdir -p "$OUT/logs"
AGENT='env -i HOME="$HOME" PATH="$PATH" USER="$USER" TERM=dumb claude -p {prompt} --permission-mode bypassPermissions --model claude-haiku-4-5-20251001 --disallowedTools WebFetch WebSearch'

one() {
  python3 -m groundhog run "$REPOS_DIR/$1" \
      --models claude-code:haiku-4.5-committed --agent-cmd "$AGENT" \
      --tasks "study/casestudy/tasks-$1.jsonl" \
      --out "$OUT/haiku-4.5-committed-$1.jsonl" \
      --commit-tests --sandbox required --timeout 300 --agent-timeout 900 --resume \
      >> "$OUT/logs/haiku-4.5-committed-$1.log" 2>&1
  echo "done $1 $(date -u '+%H:%M:%S')"
}

# Same three lanes as the case study.
( one click; one werkzeug; one attrs ) &
( one httpx; one marshmallow ) &
( one jinja; one rich ) &
wait
echo "ALL DONE $(date -u '+%H:%M:%S')"
