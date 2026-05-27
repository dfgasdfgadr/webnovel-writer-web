"""Workflow DSL engine — YAML trigger-based workflow execution."""

from app.workflows.engine import WorkflowEngine, WorkflowTrigger

__all__ = ["WorkflowEngine", "WorkflowTrigger", "get_workflow_engine"]

# Global singleton — shared across pipeline, plugins router, and API endpoints
_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    """Return the shared WorkflowEngine singleton with built-in handlers registered."""
    global _engine
    if _engine is None:
        from app.config import settings
        import os

        workflows_dir = ""
        if settings.plugins_dir:
            workflows_dir = os.path.join(settings.plugins_dir, "workflows")
        _engine = WorkflowEngine(workflows_dir=workflows_dir)

        # Register built-in action handlers
        _engine.register_handler("sim", _handle_sim_action)
        _engine.register_handler("notify", _handle_notify_action)
        _engine.register_handler("git_backup", _handle_git_backup)

        # Register built-in git_backup rule (P6-DATA04)
        _engine.rules.append(
            _engine._parse_rule({
                "trigger": "onChapterAccepted",
                "name": "章节通过后自动备份",
                "enabled": True,
                "condition": {},
                "actions": [
                    {
                        "name": "git_auto_backup",
                        "type": "git_backup",
                        "config": {"auto_init": True},
                    }
                ],
            })
        )

        # Scan plugin workflow YAML files
        _engine.scan_plugin_workflows()
    return _engine


def reset_workflow_engine() -> None:
    """Reset the singleton (for testing)."""
    global _engine
    _engine = None


async def _handle_sim_action(config: dict, context: dict) -> dict:
    """Built-in handler for simulation actions."""
    return {
        "action": "sim",
        "status": "completed",
        "mode": config.get("mode", "unknown"),
        "description": config.get("description", ""),
        "context_keys": list(context.keys()),
    }


async def _handle_notify_action(config: dict, context: dict) -> dict:
    """Built-in handler for notification actions."""
    return {
        "action": "notify",
        "status": "completed",
        "message": config.get("message", ""),
    }


async def _handle_git_backup(config: dict, context: dict) -> dict:
    """Built-in handler for git backup actions (P6-DATA02).

    Returns structured status:
    - completed: commit succeeded
    - no_changes: nothing to commit
    - skipped: not a git repo and auto_init disabled
    - error: subprocess or filesystem error
    """
    import subprocess
    import os
    from pathlib import Path
    import datetime

    project_root = context.get("project_root", "")
    chapter_num = context.get("chapter_num", "?")
    if not project_root:
        return {"action": "git_backup", "status": "skipped", "reason": "no project_root in context"}

    root = Path(project_root)
    if not root.is_dir():
        return {"action": "git_backup", "status": "skipped", "reason": "project_root not a directory"}

    git_dir = root / ".git"
    auto_init = config.get("auto_init", True)

    # Ensure git repo exists
    if not git_dir.exists():
        if not auto_init:
            return {"action": "git_backup", "status": "skipped", "reason": "not_git_repo"}
        try:
            init_res = subprocess.run(
                ["git", "init"], cwd=str(root), capture_output=True, timeout=15,
            )
            if init_res.returncode != 0:
                return {
                    "action": "git_backup",
                    "status": "error",
                    "error": f"git init failed: {init_res.stderr.decode(errors='replace')[:200]}",
                }
            # Set a default user for the auto-init repo
            subprocess.run(["git", "config", "user.email", "novelcraft@local"], cwd=str(root), capture_output=True, timeout=10)
            subprocess.run(["git", "config", "user.name", "NovelCraft"], cwd=str(root), capture_output=True, timeout=10)
        except Exception as e:
            return {"action": "git_backup", "status": "error", "error": f"git init exception: {e}"}

    # Stage and commit
    try:
        add_res = subprocess.run(
            ["git", "add", "-A"], cwd=str(root), capture_output=True, timeout=30,
        )
        commit_res = subprocess.run(
            ["git", "commit", "-m", f"auto: chapter {chapter_num} accepted"],
            cwd=str(root), capture_output=True, timeout=30,
        )

        stdout = commit_res.stdout.decode(errors="replace")[:300]
        stderr = commit_res.stderr.decode(errors="replace")[:300]

        if commit_res.returncode == 0:
            status = "completed"
            reason = None
        elif "nothing to commit" in stdout.lower() or "nothing to commit" in stderr.lower() or "no changes" in stdout.lower():
            status = "no_changes"
            reason = "nothing to commit"
        else:
            status = "error"
            reason = stderr or stdout

        result = {
            "action": "git_backup",
            "status": status,
            "project_root": str(root),
            "chapter_num": chapter_num,
            "stdout": stdout,
        }
        if reason:
            result["reason"] = reason

        # Persist execution history to .novelcraft/workflow_runs.jsonl
        _persist_workflow_run(root, {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "trigger": "onChapterAccepted",
            "action": "git_backup",
            "status": status,
            "chapter_num": chapter_num,
            "reason": reason,
        })
        return result
    except Exception as e:
        return {"action": "git_backup", "status": "error", "error": str(e)}


def _persist_workflow_run(project_root: Path, record: dict) -> None:
    """Append a workflow run record to .novelcraft/workflow_runs.jsonl."""
    import json
    try:
        nc_dir = project_root / ".novelcraft"
        nc_dir.mkdir(parents=True, exist_ok=True)
        runs_file = nc_dir / "workflow_runs.jsonl"
        with open(runs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Non-blocking: history is best-effort
        pass
