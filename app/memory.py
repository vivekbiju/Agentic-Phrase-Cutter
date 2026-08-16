import json
import os
import copy
from typing import Dict, Any


DEFAULT_MEMORY = {
    "preferences": {
        "ignore_fillers": True,
        "default_left_padding_ms": 0,
        "default_right_padding_ms": 0,
        "min_confidence_for_timing_trust": 0.75
    },
    "corrections": []
}


def fresh_default_memory() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULT_MEMORY)


def load_memory(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return fresh_default_memory()

    if os.path.getsize(path) == 0:
        return fresh_default_memory()

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return fresh_default_memory()


def save_memory(path: str, memory: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def apply_correction(memory: Dict[str, Any], phrase: str, issue: str, adjustment_ms: int) -> Dict[str, Any]:
    memory["corrections"].append({
        "phrase": phrase,
        "issue": issue,
        "adjustment_ms": adjustment_ms
    })

    issue_l = issue.lower().strip()

    # Allowing negative padding effectively trims into the STT timestamp
    if "start too early" in issue_l:
        memory["preferences"]["default_left_padding_ms"] -= adjustment_ms
    elif "start too late" in issue_l:
        memory["preferences"]["default_left_padding_ms"] += adjustment_ms
    elif "end too early" in issue_l:
        memory["preferences"]["default_right_padding_ms"] += adjustment_ms
    elif "end too late" in issue_l:
        memory["preferences"]["default_right_padding_ms"] -= adjustment_ms

    return memory
