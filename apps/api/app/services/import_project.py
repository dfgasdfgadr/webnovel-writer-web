"""Import service — scans a local directory (cyDemo style) and imports into NovelCraft."""

import json
import logging
import os
import re
import shutil
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger("novelcraft.import")


@dataclass
class ImportScanResult:
    valid: bool
    source_path: str
    errors: list[str] = field(default_factory=list)
    chapters: list[dict] = field(default_factory=list)
    settings_files: list[dict] = field(default_factory=list)
    synopsis_raw: str = ""
    story_system_files: list[str] = field(default_factory=list)
    webnovel_files: list[str] = field(default_factory=list)
    title: str = ""


REQUIRED_DIRS = ["设定集", "大纲", "正文"]
CHAPTER_PATTERN = re.compile(r"第(\d+)章[-_](.*)\.md$")


def scan_directory(source_path: str) -> ImportScanResult:
    """Scan a local directory and validate it as a Webnovel Writer project."""
    result = ImportScanResult(valid=False, source_path=source_path)
    root = Path(source_path)

    if not root.exists():
        result.errors.append(f"目录不存在: {source_path}")
        return result
    if not root.is_dir():
        result.errors.append(f"路径不是目录: {source_path}")
        return result

    # Validate required dirs
    for d in REQUIRED_DIRS:
        if not (root / d).is_dir():
            result.errors.append(f"缺少必要目录: {d}/")

    if result.errors:
        return result

    result.valid = True

    # Title from directory name
    result.title = root.name

    # Scan chapters
    chapters_dir = root / "正文"
    for f in sorted(chapters_dir.iterdir()):
        m = CHAPTER_PATTERN.match(f.name)
        if m:
            try:
                content = f.read_text(encoding="utf-8")
                result.chapters.append({
                    "number": int(m.group(1)),
                    "title": f"第{m.group(1)}章 {m.group(2).replace('.md', '')}",
                    "content": content,
                    "filename": f.name,
                    "word_count": len(content),
                })
            except Exception as e:
                result.errors.append(f"读取章节文件失败 {f.name}: {e}")

    # Scan settings
    settings_dir = root / "设定集"
    for f in settings_dir.iterdir():
        if f.suffix == ".md":
            try:
                content = f.read_text(encoding="utf-8")
                result.settings_files.append({
                    "name": f.stem,
                    "filename": f.name,
                    "content": content,
                })
            except Exception as e:
                result.errors.append(f"读取设定文件失败 {f.name}: {e}")

    # Scan synopsis
    synopsis_path = root / "大纲" / "总纲.md"
    if synopsis_path.exists():
        try:
            result.synopsis_raw = synopsis_path.read_text(encoding="utf-8")
        except Exception as e:
            result.errors.append(f"读取总纲失败: {e}")

    # Scan .story-system/
    ss_dir = root / ".story-system"
    if ss_dir.is_dir():
        for f in ss_dir.rglob("*"):
            if f.is_file():
                result.story_system_files.append(str(f.relative_to(root)))

    # Scan .webnovel/
    wn_dir = root / ".webnovel"
    if wn_dir.is_dir():
        for f in wn_dir.rglob("*"):
            if f.is_file():
                result.webnovel_files.append(str(f.relative_to(root)))

    return result


def copy_to_project(scan: ImportScanResult, target_root: str) -> list[str]:
    """Copy files from scanned directory to project root. Returns list of paths written."""
    written = []
    source = Path(scan.source_path)

    # Copy 设定集/
    for sf in scan.settings_files:
        dest = Path(target_root) / "设定集" / sf["filename"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sf["content"], encoding="utf-8")
        written.append(str(dest))

    # Copy 大纲/ (including subdirs for 卷纲, 章纲, etc.)
    outlines_source = source / "大纲"
    if outlines_source.is_dir():
        shutil.copytree(outlines_source, Path(target_root) / "大纲", dirs_exist_ok=True)
        written.append(str(Path(target_root) / "大纲"))

    # Copy 正文/ chapters
    chapters_dir = Path(target_root) / "正文"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    for ch in scan.chapters:
        dest = chapters_dir / ch["filename"]
        dest.write_text(ch["content"], encoding="utf-8")
        written.append(str(dest))

    # Copy .story-system/
    ss_source = source / ".story-system"
    if ss_source.is_dir():
        shutil.copytree(ss_source, Path(target_root) / ".story-system", dirs_exist_ok=True)
        written.append(str(Path(target_root) / ".story-system"))

    # Copy .webnovel/ → .novelcraft/ compatibility layer
    wn_source = source / ".webnovel"
    if wn_source.is_dir():
        nc_dir = Path(target_root) / ".novelcraft"
        for f in wn_source.rglob("*"):
            if f.is_file():
                rel = f.relative_to(wn_source)
                dest = nc_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                written.append(str(dest))

    return written
