"""Text splitting service for reference corpus: chapter detection and chunking."""

import re
from dataclasses import dataclass


@dataclass
class ChapterSplit:
    sequence: int
    title: str
    content: str


@dataclass
class ChunkSplit:
    sequence: int
    content: str


# Chinese numerals mapping (supports basic forms like 一, 二, 十, 十一, 二十)
_CHINESE_NUMERALS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5,
    '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10,
}


def _chinese_to_int(s: str) -> int | None:
    """Convert Chinese numeral string to integer. Supports basic forms up to ~99."""
    if not s:
        return None
    # Try Arabic numerals first
    if s.isdigit():
        return int(s)
    # Parse Chinese numerals
    total = 0
    prev = 0
    for ch in s:
        val = _CHINESE_NUMERALS.get(ch)
        if val is None:
            return None
        if val == 10:
            if prev == 0:
                total = 10
            else:
                total += prev * 10
                prev = 0
        else:
            prev = val
    total += prev
    return total if total > 0 else None


# Chinese chapter title patterns (ordered by specificity)
# Capture group 1: chapter number (supports both Arabic digits and Chinese numerals)
_CHAPTER_PATTERNS = [
    # "第123章 标题" or "第123章标题" or "第十二章 标题"
    re.compile(r'^\s*第\s*([\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千万]+)\s*章\s*[：:]?\s*(.*?)\s*$', re.MULTILINE),
    # "第123章" without title
    re.compile(r'^\s*第\s*([\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千万]+)\s*章\s*$', re.MULTILINE),
    # Markdown headers: "## 第123章 标题" or "### 第十二章"
    re.compile(r'^#{2,4}\s*第\s*([\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千万]+)\s*章\s*[：:]?\s*(.*?)\s*$', re.MULTILINE),
    # Numbered headers: "## 123. 标题" or "### 123.标题"
    re.compile(r'^#{2,4}\s*(\d+)\s*[\.．]\s+(.*?)\s*$', re.MULTILINE),
    # Bracket style: "【第123章】标题" or "（第十二章）标题"
    re.compile(r'^[【（]\s*第\s*([\d零一二三四五六七八九十壹贰叁肆伍陆柒捌玖拾百千万]+)\s*章\s*[）】]\s*(.*?)\s*$', re.MULTILINE),
]

# Fallback: any line that looks like a chapter header
_FALLBACK_PATTERN = re.compile(
    r'^\s*(?:第\s*[\d零一二三四五六七八九十]+\s*章|chapter\s+\d+|^\d+\s*[\.．]\s+\S+).*?$',
    re.MULTILINE | re.IGNORECASE,
)

_DEFAULT_CHUNK_SIZE = 800
_DEFAULT_CHUNK_OVERLAP = 100
_DEFAULT_PSEUDO_CHAPTER_SIZE = 5000


def _detect_chapter_splits(text: str) -> list[tuple[int, int, str]]:
    """Find all chapter boundaries in text.

    Returns list of (start_pos, chapter_num, title).
    """
    matches: list[tuple[int, int, str]] = []

    for pattern in _CHAPTER_PATTERNS:
        for m in pattern.finditer(text):
            raw_num = m.group(1)
            chapter_num = _chinese_to_int(raw_num)
            if chapter_num is None:
                continue
            title = (
                m.group(2).strip()
                if len(m.groups()) > 1 and m.group(2)
                else f"第{raw_num}章"
            )
            matches.append((m.start(), chapter_num, title))

    if matches:
        # Sort by position, deduplicate overlapping matches
        matches.sort(key=lambda x: x[0])
        seen_positions: set[int] = set()
        deduped: list[tuple[int, int, str]] = []
        for pos, num, title in matches:
            if any(abs(pos - p) < 3 for p in seen_positions):
                continue
            seen_positions.add(pos)
            deduped.append((pos, num, title))
        return deduped

    # No primary pattern matched — try fallback loose pattern
    fallback_matches = list(_FALLBACK_PATTERN.finditer(text))
    if len(fallback_matches) >= 2:
        seen_positions: set[int] = set()  # type: ignore[no-redef]
        deduped: list[tuple[int, int, str]] = []  # type: ignore[no-redef]
        for i, m in enumerate(fallback_matches):
            pos = m.start()
            if any(abs(pos - p) < 3 for p in seen_positions):
                continue
            seen_positions.add(pos)
            deduped.append((pos, i + 1, m.group(0).strip()))
        return deduped

    return []


def split_into_chapters(text: str) -> list[ChapterSplit]:
    """Split full text into chapters.

    Falls back to fixed-size pseudo-chapters if no headers found.
    """
    text = text.strip()
    if not text:
        return []

    splits = _detect_chapter_splits(text)

    if not splits:
        # No chapter headers found — create pseudo-chapters
        pseudo_size = _DEFAULT_PSEUDO_CHAPTER_SIZE
        chapters: list[ChapterSplit] = []
        seq = 1
        for i in range(0, len(text), pseudo_size):
            chunk = text[i : i + pseudo_size].strip()
            if chunk:
                chapters.append(
                    ChapterSplit(
                        sequence=seq,
                        title=f"伪章节 {seq}",
                        content=chunk,
                    )
                )
                seq += 1
        return chapters

    # Extract content between chapter headers
    chapters = []
    for i, (pos, num, title) in enumerate(splits):
        start = pos
        end = splits[i + 1][0] if i + 1 < len(splits) else len(text)
        content = text[start:end].strip()
        # Remove the header line itself from content to avoid duplication
        first_newline = content.find('\n')
        if first_newline != -1:
            content = content[first_newline:].strip()
        chapters.append(
            ChapterSplit(
                sequence=num,
                title=title or f"第{num}章",
                content=content,
            )
        )

    return chapters


def split_chapter_into_chunks(
    chapter_content: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkSplit]:
    """Split chapter content into overlapping chunks.

    Respects sentence boundaries where possible.
    """
    content = chapter_content.strip()
    if not content:
        return []

    if len(content) <= chunk_size:
        return [ChunkSplit(sequence=1, content=content)]

    chunks: list[ChunkSplit] = []
    seq = 1
    start = 0

    while start < len(content):
        end = min(start + chunk_size, len(content))

        if end < len(content):
            search_start = max(start + chunk_size - 50, start + overlap)
            # Prefer sentence boundary with whitespace after
            for j in range(end, search_start, -1):
                if j <= len(content) and content[j - 1] in '。！？.!?':
                    end = j
                    break
            else:
                # No sentence boundary found — break at newline if possible
                for j in range(end, search_start, -1):
                    if j < len(content) and content[j] == '\n':
                        end = j
                        break

        chunk_text = content[start:end].strip()
        if chunk_text:
            chunks.append(ChunkSplit(sequence=seq, content=chunk_text))
            seq += 1

        # Advance with overlap
        start = max(end - overlap, start + 1)

    return chunks
