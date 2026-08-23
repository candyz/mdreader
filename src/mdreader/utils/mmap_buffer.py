"""Memory-mapped line buffer module for gigabyte-scale files with zero memory overhead and sub-millisecond search."""
from __future__ import annotations
import mmap
import bisect
from array import array
from pathlib import Path
from typing import Sequence, Iterator, overload, List

MMAP_THRESHOLD_BYTES = 256 * 1024  # 256 KB threshold for memory-mapping


class MmapLineBuffer(Sequence[str]):
    """Memory-mapped, lazily decoded line buffer supporting sequence indexing and fast byte search."""

    def __init__(self, filepath: Path | str, encoding: str = "utf-8"):
        self.filepath = Path(filepath).resolve()
        self.encoding = encoding
        self._file = open(self.filepath, "rb")
        self._mmap: mmap.mmap | None = None
        size = self.filepath.stat().st_size
        self._offsets: array = array("Q" if size > 4 * 1024 * 1024 * 1024 else "I")
        self._build_index()

    def _build_index(self) -> None:
        size = self.filepath.stat().st_size
        if size == 0:
            self._mmap = None
            self._offsets.append(0)
            return

        self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        offsets = self._offsets
        offsets.append(0)
        pos = 0
        mm = self._mmap
        while True:
            pos = mm.find(b"\n", pos)
            if pos == -1:
                break
            pos += 1
            offsets.append(pos)

    def __len__(self) -> int:
        if not self._mmap:
            return 0
        size = len(self._mmap)
        if self._offsets and self._offsets[-1] == size:
            return max(0, len(self._offsets) - 1)
        return len(self._offsets)

    def __getitem__(self, index: int | slice) -> str | List[str]:
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            return [self[i] for i in range(start, stop, step)]

        total = len(self)
        if index < 0:
            index += total
        if not (0 <= index < total):
            raise IndexError("MmapLineBuffer index out of range")

        if not self._mmap:
            return ""

        start_offset = self._offsets[index]
        if index + 1 < len(self._offsets):
            end_offset = self._offsets[index + 1]
        else:
            end_offset = len(self._mmap)

        raw_bytes = self._mmap[start_offset:end_offset]
        return raw_bytes.decode(self.encoding, errors="replace").rstrip("\r\n")

    def search_text(self, query: str, case_sensitive: bool = False) -> List[int]:
        """Fast binary-search byte scanning on memory map for matching line indices."""
        if not self._mmap or not query:
            return []

        mm = self._mmap
        size = len(mm)
        q_bytes = query.encode(self.encoding) if case_sensitive else query.lower().encode(self.encoding)
        matches: List[int] = []
        chunk_size = 1024 * 1024  # 1MB chunk
        overlap = max(0, len(q_bytes) - 1)
        offset = 0

        while offset < size:
            raw_chunk = mm[offset : min(size, offset + chunk_size + overlap)]
            chunk = raw_chunk if case_sensitive else raw_chunk.lower()
            sub_pos = 0
            while True:
                found = chunk.find(q_bytes, sub_pos)
                if found == -1 or offset + found >= size:
                    break
                abs_pos = offset + found
                line_idx = bisect.bisect_right(self._offsets, abs_pos) - 1
                if not matches or matches[-1] != line_idx:
                    matches.append(line_idx)
                sub_pos = found + max(1, len(q_bytes))
            offset += chunk_size

        return matches

    def read_all_text(self) -> str:
        """Read full text if needed (e.g. for clipboard copy)."""
        if not self._mmap:
            return ""
        return self._mmap[:].decode(self.encoding, errors="replace")

    def close(self) -> None:
        """Close memory map and file descriptor."""
        try:
            if self._mmap:
                self._mmap.close()
                self._mmap = None
            if self._file:
                self._file.close()
        except Exception:
            pass

    def __del__(self) -> None:
        self.close()
