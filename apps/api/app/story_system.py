"""Story System — manages contract tree and CHAPTER_COMMIT projection.

The file-system story-system mirrors the database, providing git-friendly persistence.
"""

import json
from pathlib import Path
from typing import Any


class StorySystem:
    """Manages .story-system/ contract tree and CHAPTER_COMMIT projection chain."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root)
        self.ss_dir = self.root / ".story-system"
        self.ss_dir.mkdir(parents=True, exist_ok=True)

    # --- Contracts ---

    def master_setting(self) -> dict:
        path = self.ss_dir / "MASTER_SETTING.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def save_master_setting(self, data: dict) -> None:
        (self.ss_dir / "MASTER_SETTING.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    def volume_contract(self, vol_num: int) -> dict:
        path = self.ss_dir / "volumes" / f"volume_{vol_num:03d}.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def save_volume_contract(self, vol_num: int, data: dict) -> None:
        vdir = self.ss_dir / "volumes"
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / f"volume_{vol_num:03d}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    def chapter_contract(self, chapter_num: int) -> dict:
        path = self.ss_dir / "chapters" / f"chapter_{chapter_num:03d}.json"
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def save_chapter_contract(self, chapter_num: int, data: dict) -> None:
        cdir = self.ss_dir / "chapters"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / f"chapter_{chapter_num:03d}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

    # --- CHAPTER_COMMIT ---

    def write_commit(self, chapter_num: int, commit_data: dict) -> Path:
        cdir = self.ss_dir / "commits"
        cdir.mkdir(parents=True, exist_ok=True)
        commit_path = cdir / f"chapter_{chapter_num:03d}.commit.json"
        commit_path.write_text(json.dumps(commit_data, ensure_ascii=False, indent=2))
        return commit_path

    def write_review(self, chapter_num: int, review_data: dict) -> Path:
        rdir = self.ss_dir / "reviews"
        rdir.mkdir(parents=True, exist_ok=True)
        review_path = rdir / f"chapter_{chapter_num:03d}.review.json"
        review_path.write_text(json.dumps(review_data, ensure_ascii=False, indent=2))
        return review_path

    # --- Summaries ---

    def write_summary(self, chapter_num: int, summary: str) -> Path:
        sdir = self.root / ".novelcraft" / "summaries"
        sdir.mkdir(parents=True, exist_ok=True)
        spath = sdir / f"ch{chapter_num:04d}.md"
        spath.write_text(summary, encoding="utf-8")
        return spath

    # --- Utilities ---

    def get_all_contracts_for_writing(self, chapter_num: int, vol_num: int = 1) -> dict:
        """Collect all contracts that apply to a specific chapter."""
        master = self.master_setting()
        vol = self.volume_contract(vol_num)
        ch = self.chapter_contract(chapter_num)
        return {
            "master_setting": master,
            "volume_contract": vol,
            "chapter_contract": ch,
            "must_cover_nodes": ch.get("must_cover_nodes", []) + vol.get("must_cover_nodes", []),
            "forbidden_zones": ch.get("forbidden_zones", []) + vol.get("forbidden_zones", []),
        }

    def get_recent_summaries(self, chapter_num: int, count: int = 5) -> list[str]:
        sdir = self.root / ".novelcraft" / "summaries"
        summaries = []
        for i in range(max(1, chapter_num - count), chapter_num):
            spath = sdir / f"ch{i:04d}.md"
            if spath.exists():
                summaries.append(spath.read_text(encoding="utf-8"))
        return summaries
