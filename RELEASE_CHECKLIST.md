# Track 1 submission release

Validated source:

- `agent.py` SHA-256: `d0e03f72f69c3adcb955fe387ac88b37ee873f2dcd0fe5b60fbf2bdc40bf4b74`
- Local image: `325e/325-track1-agent:batch-v3-20260712`
- Local image ID: `sha256:960043169a81ecc65b38081632cd2552efa8f66edead66a463cf953b244ac99e`
- Platform: `linux/amd64`
- Runtime: root, no entrypoint, `CMD ["python3", "/app/agent.py"]`

Validation completed:

- 13/13 contract, routing, response-validation, and Fireworks compatibility tests pass.
- 127/127 unique public fixture prompts route to the declared category.
- 5/5 public deterministic local answers match their labels; 122 correctly require Fireworks.
- 74/74 internal fixture task IDs are present, ordered, and string typed.
- Output rows contain exactly `task_id` and `answer`.
- Root-owned `0755` output mount passes.
- Read-only root filesystem, no network, 2 CPU, and 4 GB RAM pass.
- Fireworks base and full endpoint forms pass.
- JSON-array and CSV model lists pass.
- Failed, truncated, or structurally invalid output can fall through across three allowed models.
- No credentials are embedded in the image history.

Publish from a trusted terminal only:

```bash
docker push 325e/325-track1-agent:batch-v3-20260712
docker push 325e/325-track1-agent:latest
docker manifest inspect 325e/325-track1-agent:batch-v3-20260712
docker pull --platform linux/amd64 325e/325-track1-agent:batch-v3-20260712
```

Submit this immutable reference:

```text
325e/325-track1-agent:batch-v3-20260712
```

After pushing, record the registry `RepoDigest`, update/re-save the leaderboard submission, and verify that its next state is no longer `MISSING_TASKS`.

Security prerequisite: revoke the exposed GitHub PAT and remove credentials from the local Git remote before any Git operation. Never pass Fireworks, Docker, or GitHub credentials as command-line arguments or Docker build arguments.
