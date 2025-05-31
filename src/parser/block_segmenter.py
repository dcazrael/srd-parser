import re
from typing import Tuple, List


class BlockSegmenter:
    def __init__(self, raw_text: str):
        self.raw_text = raw_text.strip()

    def extract(self) -> Tuple[List[str], str, List[str]]:
        lines: List[str] = self.raw_text.splitlines()
        header_lines: List[str] = []
        description_lines: List[str] = []
        subsection_blocks: List[str] = []

        i: int = 0
        while i < len(lines):
            line: str = lines[i].strip()
            if line.startswith("Level") or line.startswith("Cantrip") or line.startswith("**") or line == "":
                if line:
                    header_lines.append(line)
                i += 1
            else:
                break

        while i < len(lines):
            line: str = lines[i]
            if self._is_subsection_header(line):
                break
            description_lines.append(line)
            i += 1

        current_block: List[str] = []
        while i < len(lines):
            line: str = lines[i]
            if self._is_subsection_header(line):
                if current_block:
                    subsection_blocks.append(self._normalize_segment("\n".join(current_block).strip()))
                current_block = [line]
            else:
                current_block.append(line)
            i += 1
        if current_block:
            subsection_blocks.append(self._normalize_segment("\n".join(current_block).strip()))

        description: str = self._normalize_segment("\n".join(description_lines))
        return header_lines, description, subsection_blocks

    @staticmethod
    def _is_subsection_header(line: str) -> bool:
        return bool(re.match(r"\*\*.+?\*\*\.", line))

    @staticmethod
    def _normalize_segment(text: str) -> str:
        return re.sub(r"(?<!\n)\n(?!\n)", " ", text)