"""Harness state machine — deterministic workflow controller."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid
import json
from pathlib import Path


class Phase(str, Enum):
    init = "init"
    premise = "premise"
    outline = "outline"
    writing = "writing"
    maintenance = "maintenance"
    complete = "complete"


class Flow(str, Enum):
    writing = "writing"
    reviewing = "reviewing"
    rewriting = "rewriting"
    polishing = "polishing"
    simulating = "simulating"
    steering = "steering"


class Step(str, Enum):
    plan = "plan"
    context = "context"
    draft = "draft"
    review = "review"
    polish = "polish"
    extract = "extract"
    commit = "commit"
    backup = "backup"


@dataclass
class Checkpoint:
    phase: Phase
    flow: Flow
    step: Step
    chapter_id: str
    project_id: str
    payload: dict = field(default_factory=dict)


class Harness:
    """Deterministic state machine: LLM only produces content, Harness decides next step."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.state_path = self.project_root / ".novelcraft" / "state.json"
        self.checkpoint_dir = self.project_root / ".novelcraft" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {"phase": Phase.init.value, "active_flows": [], "chapter_index": 0}

    def save_state(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    def advance_step(self, chapter_id: str, project_id: str, current_step: Step, result: dict) -> Checkpoint:
        next_step = self._next_step(current_step)
        cp = Checkpoint(
            phase=Phase.writing,
            flow=Flow.writing,
            step=next_step,
            chapter_id=chapter_id,
            project_id=project_id,
            payload=result,
        )
        self._save_checkpoint(cp)
        return cp

    def _next_step(self, step: Step) -> Step:
        order = list(Step)
        idx = order.index(step)
        if idx + 1 < len(order):
            return order[idx + 1]
        return Step.backup  # loop back

    def _save_checkpoint(self, cp: Checkpoint) -> None:
        fname = f"{cp.chapter_id}_{cp.step.value}.json"
        (self.checkpoint_dir / fname).write_text(
            json.dumps({
                "phase": cp.phase.value,
                "flow": cp.flow.value,
                "step": cp.step.value,
                "chapter_id": cp.chapter_id,
                "project_id": cp.project_id,
                "payload": cp.payload,
            }, ensure_ascii=False, indent=2, default=str)
        )

    def latest_checkpoint(self, chapter_id: str) -> Checkpoint | None:
        files = sorted(self.checkpoint_dir.glob(f"{chapter_id}_*.json"))
        if not files:
            return None
        data = json.loads(files[-1].read_text())
        return Checkpoint(
            phase=Phase(data["phase"]),
            flow=Flow(data["flow"]),
            step=Step(data["step"]),
            chapter_id=data["chapter_id"],
            project_id=data["project_id"],
            payload=data.get("payload", {}),
        )
