import re
from typing import List, Tuple, Optional

from src.parser.models.spells import CastingTime, Components, SpellRange, Duration, ComponentMaterial


class SpellInfoParser:
    @staticmethod
    def parse_metadata(text) -> Tuple[int, str, List[str]]:
        match: Optional[re.Match] = re.match(r"(Cantrip|Level \d), ([^,]+), \[([^]]+)]", text,
                                             flags=re.IGNORECASE)
        if not match:
            return 0, "", []

        level_str: str
        school: str
        classes_str: str
        level: int
        classes: List[str]

        level_str, school, classes_str = match.groups()
        level = 0 if level_str.lower() == "cantrip" else int(level_str.split(" ")[1])
        classes = [c.strip() for c in classes_str.split(",")]

        return level, school, classes

    @staticmethod
    def parse_casting_time(text: str) -> CastingTime:
        lowered: str = text.lower().strip()
        type_: str | List[str]
        match: Optional[re.Match] = re.match(r"(action|bonus action|reaction)", lowered, flags=re.IGNORECASE)
        if match:
            type_ = str(match.group(1))
            return CastingTime(type=type_, cost=1)

        match: Optional[re.Match] = re.match(r"(\d+) (minute|hour)s?(?: or )?(ritual)", lowered, flags=re.IGNORECASE)
        if match:
            type_ = [match.group(2), match.group(3)]
            cost: int = int(match.group(1))
            return CastingTime(type=type_, cost=cost)
        return CastingTime(type="action", cost=1)

    @staticmethod
    def parse_components(text: str) -> Components:
        verbal: bool = "V" in text
        somatic: bool = "S" in text
        material: Optional[ComponentMaterial] = None
        material_match: Optional[re.Match] = re.search(r"\((.*?)\)", text)
        if material_match:
            material = ComponentMaterial(required=True, consumed=False,
                                         description=str(material_match.group(1).strip()))

        return Components(verbal=verbal, somatic=somatic, material=material)

    @staticmethod
    def parse_spell_range(text: str) -> SpellRange:
        match: Optional[re.Match] = re.match(r"(\d+ feet|self|touch)", text, flags=re.IGNORECASE)
        return SpellRange(type="point", distance=match.group(1) if match else "self")

    @staticmethod
    def parse_duration(text: str) -> Duration:
        lowered: str = text.lower().strip()
        if lowered.startswith("concentration"):
            match = re.search(r"up to (\d+ \w+)", lowered)
            return Duration(type="concentration", max_duration=match.group(1) if match else None)
        if lowered in {"instantaneous", "until dispelled", "until the spell ends"}:
            return Duration(type=lowered)
        return Duration(type="timed", max_duration=text.strip())