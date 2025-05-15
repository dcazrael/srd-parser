import re
from typing import Optional, Literal, List

from src.parser.models.spells import Scaling, Subsection
from src.parser.utils import DAMAGE_TYPES, TARGETS, word_to_number


class ScalingParser:
    def __init__(self, subsections: List[Subsection]):
        self.subsections: List[Subsection] = subsections
        self.damage_pattern: str = "|".join(DAMAGE_TYPES)
        self.target_pattern: str = "|".join(TARGETS)

    def parse(self) -> Optional[Scaling]:
        match: Optional[re.Match]

        for section in self.subsections:
            if "higher-level spell slot" in section.name.lower():
                return self._match_slot_level(section.text.lower())
            elif "cantrip upgrade" in section.name.lower():
                return self._match_level_threshold(section.text.lower())

        return None

    def _match_slot_level(self, search_text: str) -> Scaling|None:
        mode: Literal["slot_level", "level_threshold"] = "slot_level"

        match = re.search(rf"target one additional ({self.target_pattern}) for each .*? level above (\d+)", search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(2)),
                per_level=None,
                per_slot={"effect": "target", "value": 1, "target_type": match.group(1)}
            )

        match = re.search(r"(damage|healing) increases by (\d+d\d+) for each .*? level above (\d+)", search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(3)),
                per_level=None,
                per_slot={"effect": match.group(1), "value": match.group(2)}
            )

        match = re.search(r"duration increases by (\d+) (minute|hour)s? for each .*? level above (\d+)", search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(3)),
                per_level=None,
                per_slot={"effect": "duration", "value": int(match.group(1)), "duration_type": match.group(2)}
            )

        match = re.search(rf"({self.damage_pattern}) damage increases by (\d+d\d+) for each .*? level above (\d+)",
                          search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(3)),
                per_level=None,
                per_slot={"effect": "damage", "value": match.group(2), "damage_type": match.group(1)}
            )

        match = re.search(r"healing increases by (\d+) for each .*? level above (\d+)", search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(2)),
                per_level=None,
                per_slot={"effect": "healing", "value": int(match.group(1))}
            )

        match = re.search(r"hit points increase by (\d+) for each .*? level above (\d+)", search_text)
        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(2)),
                per_level=None,
                per_slot={"effect": "hit_points", "value": int(match.group(1))}
            )

        # The damage (both initial and later) increases by 1d4 for each spell slot level above 2
        match = re.search(r"damage \(both initial and later\) increases by (\d+d\d+) for each .*? level above (\d+)",
                          search_text)

        if match:
            return Scaling(
                mode=mode,
                base_level=int(match.group(2)),
                per_level=None,
                per_slot={"effect": "damage", "value": match.group(1)}
            )
        return None

    def _match_level_threshold(self, search_text: str) -> Scaling|None:
        mode: Literal["slot_level", "level_threshold"] = "level_threshold"
        per_level: dict[str, str | List[dict[str, int | str]]] = {"effect": "", "values": None}

        match = re.search(
            rf"(\b{self.damage_pattern}\b\s?)? (damage|range)? (?:increases by \d+d\d+|doubles)?\s?when you reach levels (\d+) \(([^)]+)\), (\d+) \(([^)]+)\), and (\d+) \(([^)]+)\)",
            search_text)

        values: List[dict[str, int | str]]
        if match:
            group_map = [
                (int(match.group(3)), match.group(4)),
                (int(match.group(5)), match.group(6)),
                (int(match.group(7)), match.group(8)),
            ]
            if "damage" in (match.group(2) or ""):
                values = [{"level": lvl, "dice": val} for lvl, val in group_map]
            else:
                values = [{"level": lvl, "mod": val} for lvl, val in group_map]
            per_level = {"effect": str(match.group(2)),
                         "damage_type": match.group(1) if match.group(
                             1) else "", "values": values}

        matches = re.findall(
            rf"(two|three|four) beams at level (\d+)",
            search_text)

        if matches:
            values = [{"level": int(lvl), "beams": word_to_number(word)} for word, lvl in matches]

            per_level = {"effect": "beams", "values": values}

        # The spell creates two beams at level 5, three beams at level 11, and four beams at level 17
        if match or matches:
            return Scaling(
                mode=mode,
                base_level=1,
                per_level=per_level,
                per_slot=None
            )
        return None