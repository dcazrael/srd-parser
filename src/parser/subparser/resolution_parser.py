import re
from typing import Optional, Literal, cast

from src.parser.models.spells import Resolution
from src.parser.subparser.base_parser import TextParserBase


class ResolutionParser(TextParserBase):
    def parse(self) -> Optional[Resolution]:
        if "saving throw" in self.text:
            match: Optional[re.Match] = re.search(
                r"(strength|dexterity|constitution|intelligence|wisdom|charisma) saving throw",
                self.text
            )
            if match:
                ability: Literal["str", "dex", "con", "int", "wis", "cha"] = cast(
                    Literal["str", "dex", "con", "int", "wis", "cha"],
                    match.group(1).lower()[:3]
                )
                return Resolution(type="saving_throw", save_type=ability)
            return Resolution(type="saving_throw")

        if "make an attack roll" in self.text or "ranged spell attack" in self.text:
            return Resolution(type="attack_roll")

        return Resolution(type="automatic")