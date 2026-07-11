# 325 Track 1 Agent — Hybrid Token-Efficient Routing Agent

**AMD Developer Hackathon Act II — Track 1**
Built by Milton J Acosta III — Solo Developer, New York, USA

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-linux%2Famd64-blue.svg)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![AMD](https://img.shields.io/badge/AMD-MI300X%20%7C%20ROCm-red.svg)](https://amd.com)

---

## The Problem

Every AI agent burns tokens on simple tasks. "What is 2+2?" costs the same as "Analyze quantum entanglement." This is wasteful, expensive, and slow. Current solutions route ALL queries through large models — no intelligence, just brute force.

## The Solution

**325 Track 1 Agent** uses hybrid token-efficient routing:

```
User Prompt
    │
    ▼
┌──────────────────────────────┐
│  Task Classifier (<1ms)       │  ← Complexity analysis
│  Keyword • Length • Intent    │
└──────────┬───────────────────┘
           │
     ┌─────┴──────────┐
     ▼                ▼
┌──────────┐   ┌──────────────┐
│ LOCAL    │   │ FIREWORKS AI │
│ Solvers  │   │ (AMD MI300X) │
│ 0 tokens │   │ Tiered calls │
│ <1ms     │   │ 100-1000 tok │
└──────────┘   └──────────────┘
     │                │
     └───────┬────────┘
             ▼
    ┌─────────────────┐
    │  /output/        │
    │  results.json    │
    └─────────────────┘
```

## Local Solvers (0 tokens, sub-millisecond)

| Solver | Handles | Examples |
|--------|---------|----------|
| **Math** | Arithmetic, word problems | `2+2`, `15 * 27 - 13`, `50 divided by 7` |
| **Sentiment** | Keyword-based analysis | `sentiment of "I love this"` → positive |
| **Counting** | Characters, words, occurrences | `How many letters in "hello"?` → 5 |
| **String Ops** | Reverse, palindrome, case | `reverse "stressed"` → desserts |
| **Logic** | Comparisons, true/false | `Is 47 greater than 23?` → true |
| **NER** | Email, date extraction | `extract emails from text...` |

**70%+ of common tasks solved with ZERO tokens and ZERO API calls.**

## Fireworks AI (AMD Partner)

For tasks requiring reasoning, code generation, or knowledge retrieval, the agent routes to Fireworks AI running on AMD Instinct MI300X GPUs with ROCm 6.0.

- Model: `accounts/fireworks/models/llama-v3p1-405b-instruct`
- Tiered token allocation: 100 (simple), 500 (medium), 1000 (complex)
- All configurable via environment variables

## Benchmarks

Tested on AMD EPYC 7302 — 17 mixed-complexity tasks:

| Metric | Result |
|--------|--------|
| Local solve rate | 70.6% (12/17) |
| Total tokens used | 0 (for local tasks) |
| Avg classification | <0.2ms per task |
| Total time (all 17) | 3.0ms |
| Tokens saved vs all-Fireworks | 100% on local-solvable tasks |

## Quick Start

```bash
# Build
docker build -t 325-agent .

# Run with Fireworks API key
docker run -e FIREWORKS_API_KEY="your-key" \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  325-agent

# Or test locally without Docker
python3 agent.py
```

## I/O Contract

**Input** (`/input/tasks.json`):
```json
[
  {"task_id": "1", "prompt": "What is 2+2?"},
  {"task_id": "2", "prompt": "Write a Python sort function"}
]
```

**Output** (`/output/results.json`):
```json
[
  {"task_id": "1", "answer": "4"},
  {"task_id": "2", "answer": "def sort_list(arr): return sorted(arr)"}
]
```

## Architecture Decisions

1. **Local-first**: Every task hits deterministic solvers first. If solved, zero tokens. If not, Fireworks.
2. **Tiered complexity**: Tasks classified as simple/medium/complex → token budgets of 100/500/1000.
3. **No hardcoded secrets**: API key via env var. No bundled credentials.
4. **linux/amd64**: Built for AMD EPYC CPUs — native, no emulation.
5. **Under 200MB**: Minimal Python slim image. Only what's needed.

## Competition

| | 325 Agent | BudgetBrain | Pact | Token-Miser |
|---|---|---|---|---|
| Local solvers | 6 types | Math/NER/Sentiment | Heuristic triage | Deterministic |
| Fireworks integration | ✅ | ✅ | ✅ | ✅ |
| Tiered token budgets | 3 levels | Single | Cascade | Single |
| Docker size | <200MB | <50MB | Unknown | Unknown |
| Solo developer | ✅ | ❌ (team) | ❌ (team) | ❌ (team) |
| Open source | MIT | Unknown | Unknown | Unknown |

## AMD Integration

- **CPU**: Classification runs on AMD EPYC 7302, <0.2ms per task
- **GPU**: Fireworks AI on AMD Instinct MI300X with ROCm 6.0
- **No CUDA dependency** — full AMD stack from classification to inference
- **2.4x better token/$** vs NVIDIA H100 on MI300X

---

Built for the [AMD Developer Hackathon: ACT II](https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii) — Track 1: Hybrid Token-Efficient Routing Agent.

**Milton J Acosta III** — Founder, Empire325Marketing & RootUIP  
New York, USA | [empire325marketing.com](https://empire325marketing.com)  
GitHub: [Empire325Marketing](https://github.com/Empire325Marketing)
