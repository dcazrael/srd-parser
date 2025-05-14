import re
from typing import Any, List, Dict, Optional

from src.parser.models.spells import Subsection


class SectionParser:
    def __init__(self, raw_text: str):
        self.raw_text: str = raw_text

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
        lines: List[str] = self.raw_text.strip().splitlines()
        current_field: str = "description"
        current_sub: Optional[Subsection] = None

        for line in lines:
            stripped: str = line.strip()
            match: Optional[re.Match] = re.match(r"\*\*(.+?)\*\*[:.] ?(.*)", stripped)
            if match:
                field_name:str = str(match.group(1).strip())
                field_value:str = str(match.group(2).strip())

                if field_name in known_fields:
                    current_field = field_name
                    sections[current_field] = field_value
                    continue

                if "Higher-Level Spell Slot" in field_name or "Cantrip Upgrade" in field_name:
                    sections["scales_with"] = f"{field_name} {field_value}"
                    continue

                if current_sub:
                    sections["subsections"].append(current_sub)

                current_sub = Subsection(name=field_name, text=field_value)
                current_field = "description"
                continue

            else:
                if current_sub:
                    current_sub.text += "\n" + line if current_sub.text else line
                else:
                    current_field = "description"

            sections[current_field] += ("\n" + line if sections[current_field] else line)

        if current_sub:
            sections["subsections"].append(current_sub)

        return sections