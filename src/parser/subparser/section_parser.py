import re
from typing import Any, List, Dict, Optional

from src.parser.models.spells import Subsection, CastingTime


class SectionParser:
    def __init__(self, header_lines: List[str], subsection_blocks: List[str]):
        self.header_lines: List[str] = header_lines
        self.subsection_blocks: List[str] = subsection_blocks

    def parse(self) -> Dict[str, Any]:
        sections: Dict[str, Any] = {
            "Casting Time": "",
            "Range": "",
            "Components": "",
            "Duration": "",
            "description": "",
            "scales_with": "",
            "subsections": []
        }

        known_fields: set[str] = {"Casting Time", "Range", "Components", "Duration"}


        for line in self.header_lines:
            stripped: str = line.strip()
            match: Optional[re.Match] = re.match(r"\*\*(.+?)\*\*[:.] ?(.*)", stripped)

            if not match:
                continue

            field_name:str = str(match.group(1).strip())
            field_value:str = str(match.group(2).strip())

            if field_name in known_fields:
                sections[field_name] = field_value

            elif "Higher-Level Spell Slot" in field_name or "Cantrip Upgrade" in field_name:
                sections["scales_with"] = f"{field_name} {field_value}"

        sections["subsections"] = [
            Subsection(name=self._extract_name(block), text=self._strip_subsection_header(block))
            for block in self.subsection_blocks
        ]

        return sections

    @staticmethod
    def _extract_name(text: str) -> str:
        first_line: str = text.strip().split("\n", 1)[0]
        match: Optional[re.Match] = re.match(r"\*\*(.+?)\*\*\.", first_line.strip())
        return str(match.group(1).strip()) if match else "Unnamed"

    @staticmethod
    def _strip_subsection_header(text: str) -> str:
        lines: List[str] = text.strip().splitlines()
        if not lines:
            return ""
        first_line:str = lines[0]
        match = re.match(r"\*\*(.+?)\*\*\.\s*(.*)", first_line.strip())
        body_lines: List[str] = lines[1:]
        if match:
            inline_body = match.group(2)
            return " ".join([inline_body] + body_lines).strip()
        return "\n".join(lines[1:]).strip()
