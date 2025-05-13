# parser/old_spell_parser.py
import re
from .models.spells.base import Spell, SpellSubsection
from typing import List, Any

FIELD_MAP = ["Casting Time", "Range", "Components", "Duration"]

class SpellParser:
    def __init__(self, text: str):
        self.text = text
        self.spells: List[Spell] = []

    def parse(self):
        start = self.text.find("#### ")
        if start != -1:
            self.text = self.text[start:]

        raw_blocks = re.split(r"^#### (.+)", self.text, flags=re.MULTILINE)
        for i in range(1, len(raw_blocks), 2):
            name = raw_blocks[i].strip()
            body = raw_blocks[i + 1]
            spell = self.parse_single_spell(name, body)
            self.spells.append(spell)

    def parse_single_spell(self, name: str, body: str) -> Spell:
        lines = body.strip().split("\n")
        meta_line = lines.pop(0)
        level, school, classes = self._parse_metadata(meta_line)
        sections = self._extract_sections("\n".join(lines))
        return Spell(
            name=name,
            level=level,
            school=school,
            classes=classes,
            casting_time=sections.get("Casting Time", ""),
            range=sections.get("Range", ""),
            components=sections.get("Components", ""),
            duration=sections.get("Duration", ""),
            description=sections.get("description", "").strip(),
            higher_levels=sections.get("higher_levels", ""),
            subsections=sections.get("subsections", [])
        )

    @staticmethod
    def _parse_metadata(line: str):
        match = re.match(r"(Cantrip|Level \d), ([^,]+), \[([^]]+)]", line)
        if not match:
            return None, None, []
        level_str, school, classes_str = match.groups()
        level = 0 if level_str == "Cantrip" else int(level_str.split(" ")[1])
        classes = [c.strip() for c in classes_str.split(",")]
        return level, school, classes

    @staticmethod
    def _extract_sections(text: str) -> dict[str, Any]:
        sections: dict[str, Any] = {key: "" for key in FIELD_MAP}
        sections["description"] = ""
        sections["subsections"] = []
        sections["higher_levels"] = ""

        lines = text.strip().splitlines()
        current = "description"
        known_field_started = False

        for line in lines:
            stripped = line.strip()

            # Standardfeld erkennen
            match = re.match(r"\*\*(.+?)\*\*: ?(.*)", stripped)
            if match:
                field_name, field_value = match.group(1).strip(), match.group(2).strip()
                if field_name in FIELD_MAP:
                    current = field_name
                    known_field_started = True
                    sections[current] = field_value
                    continue

            # Inline Subsections oder Higher-Level Slot erkennen
            inline_match = re.match(r"\*\*(.+?)\*\*[.:]?\s*(.+)", stripped)
            if inline_match:
                title = inline_match.group(1).strip()
                content = inline_match.group(2).strip()

                if title == "Using a Higher-Level Spell Slot":
                    sections["higher_levels"] = content
                else:
                    sections["subsections"].append(SpellSubsection(
                        name=title,
                        content=content,
                        type="inline"
                    ))
                continue

            # Blockwechsel nach Feldende → Beschreibung starten
            if known_field_started and current in FIELD_MAP and not stripped.startswith("**"):
                current = "description"
                known_field_started = False

            # Zeile anhängen
            sections[current] += ("\n" + line if sections[current] else line)

        return sections