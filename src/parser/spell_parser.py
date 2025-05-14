import re
from dataclasses import asdict
from typing import List, Dict, Any, Optional, Literal, cast, Tuple, Set
from .models.spells import Components, ComponentMaterial, CastingTime, ConditionEffect, EndCondition, Effect, Duration, \
    Requirements, SpellRange, Spell, Scaling, SaveInfo, Targeting, Resolution, DamageInstance, AreaShape, Subsection
from .subparser.effect_parser import EffectParser
from .subparser.section_parser import SectionParser
from .subparser.targeting_parser import TargetingParser


class SpellParser:
    def __init__(self, text: str):
        self.text: str = text
        self.spells: List[Spell] = []

        self.DAMAGE_TYPES: List[str] = [
            "base", "initial", "acid", "fire", "cold", "lightning", "radiant", "necrotic",
            "force", "thunder", "psychic", "poison", "bludgeoning", "piercing", "slashing"
        ]

    def parse(self):
        start: int = self.text.find("#### ")
        if start == -1:
            self.text = self.text[start:]

        raw_blocks: List[str] = re.split(r"^#### (.+)", self.text, flags=re.MULTILINE)
        for i in range(1, len(raw_blocks), 2):
            name: str = raw_blocks[i].strip()
            body: str = raw_blocks[i + 1]
            spell: Spell = self.parse_single_spell(name, body)
            self.spells.append(spell)

    def parse_single_spell(self, name: str, body: str) -> Spell:

        print(name)
        lines: List[str] = body.strip().split("\n")
        meta_line: str = lines.pop(0)
        level: int
        school: str
        classes: List[str]
        level, school, classes = self._parse_metadata(meta_line)
        sections: Dict[str, Any] = SectionParser("\n".join(lines)).parse()

        description: str = re.sub(r"\n(?=\w)", " ", sections.get("description", "").strip())
        casting_time: CastingTime = self._parse_casting_time(sections.get("Casting Time", ""))
        components: Components = self._parse_components(sections.get("Components", ""))
        spell_range: SpellRange = self._parse_spell_range(sections.get("Range", ""))
        duration: Duration = self._parse_duration(sections.get("Duration", ""))
        effects: List[Effect] = EffectParser(description).parse()
        targeting: Targeting = TargetingParser(description).parse()
        save: Optional[SaveInfo] = self._parse_save(description)
        scaling: Optional[Scaling] = self._parse_scaling(sections['scales_with'])
        requirements: Optional[Requirements] = self._parse_requirements(description)

        return Spell(
            name=name,
            level=level,
            school=school,
            classes=classes,
            casting_time=casting_time,
            range=spell_range,
            components=components,
            duration=duration,
            description=description,
            targeting=targeting,
            effects=effects,
            save=save,
            scaling=scaling,
            requirements=requirements,
            subsections=sections.get("subsections", []),
            tags=[]
        )

    @staticmethod
    def _parse_metadata(line: str) -> tuple[int, str, List[str]]:
        match: Optional[re.Match] = re.match(r"(Cantrip|Level \d), ([^,]+), \[([^]]+)]", line, flags=re.IGNORECASE)
        if not match:
            return 0, "", []
        level_str, school, classes_str = match.groups()
        level: int = 0 if level_str == "Cantrip" else int(level_str.split(" ")[1])
        classes: List[str] = [c.strip() for c in classes_str.split(",")]
        return level, school, classes

    @staticmethod
    def _parse_casting_time(text: str) -> CastingTime:
        lowered: str = text.lower().strip()
        type_: str|List[str]
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
    def _parse_components(text: str) -> Components:
        verbal: bool = "V" in text
        somatic: bool = "S" in text
        material: Optional[ComponentMaterial] = None
        material_match: Optional[re.Match] = re.search(r"\((.*?)\)", text)
        if material_match:
            material = ComponentMaterial(required=True, consumed=False,
                                         description=str(material_match.group(1).strip()))

        return Components(verbal=verbal, somatic=somatic, material=material)

    @staticmethod
    def _parse_spell_range(text: str) -> SpellRange:
        match: Optional[re.Match] = re.match(r"(\d+ feet|self|touch)", text, flags=re.IGNORECASE)
        return SpellRange(type="point", distance=match.group(1) if match else "self")

    @staticmethod
    def _parse_duration(text: str) -> Duration:
        lowered: str = text.lower().strip()
        if lowered.startswith("concentration"):
            match = re.search(r"up to (\d+ \w+)", lowered)
            return Duration(type="concentration", max_duration=match.group(1) if match else None)
        if lowered in {"instantaneous", "until dispelled", "until the spell ends"}:
            return Duration(type=lowered)
        return Duration(type="timed", max_duration=text.strip())

    @staticmethod
    def _parse_resolution(text: str) -> Optional[Resolution]:
        lowered: str = text.lower().strip()
        if "saving throw" in lowered:
            match = re.search(
                r"(strength|dexterity|constitution|intelligence|wisdom|charisma) saving throw",
                lowered,
                re.IGNORECASE
            )
            if match:
                ability: Literal["str", "dex", "con", "int", "wis", "cha"] = cast(
                    Literal["str", "dex", "con", "int", "wis", "cha"], match.group(1).lower()[:3])
                return Resolution(type="saving_throw", save_type=ability)
            return Resolution(type="saving_throw")
        if "make an attack roll" in lowered:
            return Resolution(type="attack_roll")
        return Resolution(type="automatic")

    @staticmethod
    def _parse_save(text: str) -> Optional[SaveInfo]:
        match: Optional[re.Match] = re.search(
            r"(strength|dexterity|constitution|intelligence|wisdom|charisma) saving throw", text, re.IGNORECASE)
        if match:
            negates = not bool(
                re.search(r"half (as much )?damage|take half damage|only take half", text, re.IGNORECASE))
            save_type: Literal["str", "dex", "con", "int", "wis", "cha"] = cast(
                Literal["str", "dex", "con", "int", "wis", "cha"], match.group(1).lower()[:3])
            return SaveInfo(type=save_type, dc_source="spellcasting", negates=negates)
        return None

    def _parse_scaling(self, text: str) -> Optional[Scaling]:
        possible_targets: List[str] = ["creature", "humanoid", "beast"]
        target_pattern: str = "|".join(possible_targets)
        damage_pattern: str = "|".join(self.DAMAGE_TYPES)
        lowered: str = text.lower()
        match: Optional[re.Match]
        mode: Literal["slot_level", "level_threshold"] = "level_threshold"
        per_level: dict[str, str | List[dict[str, int | str]]]

        if "using a higher-level spell slot" in lowered:
            mode = "slot_level"
            match = re.search(rf"target one additional ({target_pattern}) for each .*? level above (\d+)", lowered)
            if match:
                return Scaling(
                    mode=mode,
                    base_level=int(match.group(2)),
                    per_level=None,
                    per_slot={"effect": "target", "value": 1, "target_type": match.group(1)}
                )

            match = re.search(r"(damage|healing) increases by (\d+d\d+) for each .*? level above (\d+)", lowered)
            if match:
                return Scaling(
                    mode=mode,
                    base_level=int(match.group(3)),
                    per_level=None,
                    per_slot={"effect": match.group(1), "value": match.group(2)}
                )

            match = re.search(r"duration increases by (\d+) (minute|hour)s? for each .*? level above (\d+)", lowered)
            if match:
                return Scaling(
                    mode=mode,
                    base_level=int(match.group(3)),
                    per_level=None,
                    per_slot={"effect": "duration", "value": int(match.group(1)), "duration_type": match.group(2)}
                )

            match = re.search(rf"({damage_pattern}) damage increases by (\d+d\d+) for each .*? level above (\d+)",
                              lowered)
            if match:
                return Scaling(
                    mode=mode,
                    base_level=int(match.group(3)),
                    per_level=None,
                    per_slot={"effect": "damage", "value": match.group(2), "damage_type": match.group(1)}
                )

            match = re.search(r"healing increases by (\d+) for each .*? level above (\d+)", lowered)
            if match:
                return Scaling(
                    mode=mode,
                    base_level=int(match.group(2)),
                    per_level=None,
                    per_slot={"effect": "healing", "value": int(match.group(1))}
                )

        elif "cantrip upgrade" in lowered:
            match = re.search(rf"(\b{damage_pattern}\b\s?)? (damage|range)? (?:increases by \d+d\d+|doubles)?\s?when you reach levels (\d+) \(([^)]+)\), (\d+) \(([^)]+)\), and (\d+) \(([^)]+)\)",
                lowered)

            values: List[dict[str, int | str]] = []
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
                lowered)

            if matches:
                word_to_num = {"two": 2, "three": 3, "four": 4}
                values = [{"level": int(lvl), "beams": word_to_num[word]} for word, lvl in matches]

                per_level = {"effect": "beams", "values": values}

            #The spell creates two beams at level 5, three beams at level 11, and four beams at level 17
            if match or matches:
                return Scaling(
                    mode=mode,
                    base_level=1,
                    per_level=per_level,
                    per_slot=None
                )
        return None

    @staticmethod
    def _parse_requirements(text: str) -> Requirements:
        breath: bool = "verbal" in text.lower()
        hands: int = 1 if "somatic" in text.lower() else 0
        return Requirements(breath_required=breath, hands_free=hands)
