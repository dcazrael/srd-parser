import re
from typing import Optional, Literal, cast

from src.parser.models.spells import SaveInfo
from src.parser.subparser.base_parser import TextParserBase


class SaveParser(TextParserBase):
    def parse(self) -> Optional[SaveInfo]:
        match: Optional[re.Match] = re.search(
            r"(strength|dexterity|constitution|intelligence|wisdom|charisma) saving throw", self.text)
        if match:
            negates = not bool(
                re.search(r"half (as much )?damage|take half damage|only take half", self.text))
            save_type: Literal["str", "dex", "con", "int", "wis", "cha"] = cast(
                Literal["str", "dex", "con", "int", "wis", "cha"], match.group(1).lower()[:3])
            return SaveInfo(type=save_type, dc_source="spellcasting", negates=negates)
        return None