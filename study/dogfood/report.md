### Groundhog on Groundhog, 2026-09-26

| Model | Solved | Pass rate | 95% CI | F2P-only | Collateral | Cost | Median |
|---|---:|---:|---|---:|---|---:|---:|
| claude-code | 10/10 | 100% | 72% – 100% | 10/10 | 0 | - | 222s |
| ollama:qwen3:8b | 1/10 | 10% | 2% – 40% | 1/10 | 0 | $0.00 | 676s |

<details><summary>Per task</summary>

| Task | claude-code | qwen3:8b |
|---|:---:|:---:|
| Say out loud when pyproject.toml could not be parsed | ✅ | ❌ |
| --system-prompt for the built-in loop, --sample N --seed S f | ✅ | ❌ |
| groundhog doctor: one screen that says what to install | ✅ | ✅ |
| --jobs N: run attempts concurrently | ✅ | ❌ |
| An external agent with no tool record is not a failed measur | ✅ | ❌ |
| Rust: detect Cargo.toml, name integration-test targets, pars | ✅ | ❌ |
| Report what a FAIL_TO_PASS-only harness would have said, nex | ✅ | ❌ |
| groundhog bench <repo>: mine, validate, run and report in on | ✅ | ❌ |
| report --markdown and --json, and a badge command for README | ✅ | ❌ |
| validate --stability N: reject tasks whose tests flip betwee | ✅ | ❌ |

</details>
