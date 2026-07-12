# Accuracy and release evidence

Validated on July 12, 2026 against `agent.py` SHA-256
`d0e03f72f69c3adcb955fe387ac88b37ee873f2dcd0fe5b60fbf2bdc40bf4b74` and local image
`325e/325-track1-agent:batch-v3-20260712`.

## Proven locally

- 13/13 contract, routing, API-compatibility, response-validation, and regression tests pass.
- 127/127 unique prompts across all 11 discoverable BudgetBrain public fixture files route to the declared category.
- 5/5 prompts accepted by deterministic local solvers match the public expected-answer constraints.
- The other 122/127 public prompts deliberately route to Fireworks instead of receiving an unsafe heuristic answer.
- A fake OpenAI-compatible proxy verifies `/v1/chat/completions`, CSV/JSON model configuration, model fallback, and output normalization.
- The exact Docker image exits successfully in 0.83 seconds on the 74-task internal fixture under 2 CPUs, 4 GB RAM, no network, a read-only root filesystem, and a root-owned `0755` output mount.
- Docker output contains 74/74 ordered task IDs and exactly the required string fields `task_id` and `answer`.
- Host and in-image `agent.py` hashes match; the image is `linux/amd64`, runs as root, has no `ENTRYPOINT`, and uses `CMD ["python3", "/app/agent.py"]`.

Reproduce the public fixture audit with:

```bash
python3 audit_public_fixtures.py /path/to/BudgetBrain/eval/fixtures
python3 -m unittest -v test_batch_contract.py
```

## Not provable locally

The current host has no `FIREWORKS_API_KEY`, `FIREWORKS_BASE_URL`, or `ALLOWED_MODELS`, so real model-answer accuracy was not measured. Public-fixture routing is 127/127, but 122 answers depend on the scorer-provided Fireworks runtime. Hidden leaderboard accuracy and podium placement therefore cannot be honestly guaranteed before scoring.

The client now reduces that risk by selecting category-appropriate allowed models, rejecting truncated or structurally invalid responses, enforcing common sentiment/summary/code/SQL/JSON constraints, and trying up to three allowed models within a global runtime deadline.
