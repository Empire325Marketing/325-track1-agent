"""Audit routing and deterministic answers against public Track 1-style fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import agent


def answer_matches(task: dict, answer: str) -> bool:
    normalized = answer.strip().lower()
    if "expected" in task and normalized != str(task["expected"]).strip().lower():
        return False
    if any(str(value).lower() not in normalized for value in task.get("contains", [])):
        return False
    contains_any = task.get("contains_any", [])
    if contains_any and not any(str(value).lower() in normalized for value in contains_any):
        return False
    for group in task.get("contains_any_groups", []):
        if not any(str(value).lower() in normalized for value in group):
            return False
    return True


def audit(fixtures: Path) -> dict:
    unique: dict[tuple[object, object], tuple[str, dict]] = {}
    for path in sorted(fixtures.glob("*.json")):
        try:
            tasks = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            if isinstance(task, dict) and "prompt" in task and "category" in task:
                unique[(task.get("task_id"), task["prompt"])] = (path.name, task)

    category_failures = []
    local_failures = []
    local_count = 0
    for filename, task in unique.values():
        category = agent.infer_task_category(task["prompt"])
        if category != task["category"]:
            category_failures.append({
                "fixture": filename,
                "task_id": task.get("task_id"),
                "expected": task["category"],
                "actual": category,
            })
        result = agent.process_task(task)
        if result["route"] == "local":
            local_count += 1
            if not answer_matches(task, result["answer"]):
                local_failures.append({
                    "fixture": filename,
                    "task_id": task.get("task_id"),
                    "answer": result["answer"],
                })

    source_hash = hashlib.sha256(Path(agent.__file__).read_bytes()).hexdigest()
    return {
        "agent_sha256": source_hash,
        "unique_public_prompts": len(unique),
        "category_matches": len(unique) - len(category_failures),
        "category_failures": category_failures,
        "deterministic_local_answers": local_count,
        "deterministic_local_correct": local_count - len(local_failures),
        "local_failures": local_failures,
        "fireworks_required": len(unique) - local_count,
        "limitation": "Remote Fireworks answer accuracy and hidden leaderboard accuracy are not measured.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixtures", type=Path)
    args = parser.parse_args()
    report = audit(args.fixtures)
    print(json.dumps(report, indent=2))
    return 1 if report["category_failures"] or report["local_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
