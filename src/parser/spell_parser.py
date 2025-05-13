import re
from typing import List, Dict, Any, Optional, Literal, cast, Tuple
from .models.spells import Components, ComponentMaterial, CastingTime, ConditionEffect, EndCondition, Effect, Duration, \
    Requirements, SpellRange, Spell, Scaling, SaveInfo, Targeting, Resolution, DamageInstance, AreaShape, Subsection


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
        lines: List[str] = body.strip().split("\n")
        meta_line: str = lines.pop(0)
        level: int
        school: str
        classes: List[str]
        level, school, classes = self._parse_metadata(meta_line)
        sections: Dict[str, Any] = self._extract_sections("\n".join(lines))

        description: str = sections.get("description", "").strip()
        casting_time: CastingTime = self._parse_casting_time(sections.get("Casting Time", ""))
        components: Components = self._parse_components(sections.get("Components", ""))
        spell_range: SpellRange = self._parse_spell_range(sections.get("Range", ""))
        duration: Duration = self._parse_duration(sections.get("Duration", ""))
        effects: List[Effect] = self._parse_effects(description)
        targeting: Targeting = self._parse_targeting(description)
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
    def _extract_sections(text: str) -> Dict[str, Any]:
        sections: Dict[str, Any] = {"Casting Time": "", "Range": "", "Components": "", "Duration": "",
                                    "description": "", "subsections": []}
        known_fields: set[str] = {"Casting Time", "Range", "Components", "Duration"}
        lines: List[str] = text.strip().splitlines()
        current_field: str
        current_sub: Optional[Subsection] = None

        for line in lines:
            stripped: str = line.strip()
            match: Optional[re.Match] = re.match(r"\*\*(.+?)\*\*[:.] ?(.*)", stripped)
            if match:
                field_name: str = str(match.group(1).strip())
                field_value: str = str(match.group(2).strip())
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
    def _parse_targeting(text: str) -> Targeting:
        lowered: str = text.lower().strip()
        targeting_type: str = "creature"
        filters: Optional[List[str]] = []
        count: Optional[int] = None
        shape: Literal["sphere", "cube", "line", "cone", "cylinder"] = "sphere"
        size: Optional[int] = None  # für cube: edge length, sphere: diameter
        length: Optional[int] = None  # für line, cone
        width: Optional[int] = None  # für line
        radius: Optional[int] = None  # für sphere, cylinder
        height: Optional[int] = None  # für cylinder
        angle: Optional[int] = None  # für cone
        area: Optional[AreaShape] = None

        shape_str: str

        if "self" in lowered:
            targeting_type = "self"
        elif "touch" in lowered:
            targeting_type = "touch"

        filter_match: Optional[re.Match] = re.search(r"targets? (\w+)", lowered, re.IGNORECASE)
        if filter_match:
            filters = [str(filter_match.group(1))]

        count_match: Optional[re.Match] = re.search(r"(\d+) (creature|target)", lowered, re.IGNORECASE)
        if count_match:
            count = int(count_match.group(1))

        area_match: Optional[re.Match] = re.search(r"(\d+)-foot(?:-radius)? (sphere|cube|line|cone|cylinder)", lowered, re.IGNORECASE)
        if area_match:
            targeting_type = "area"
            shape_str = str(area_match.group(2))

            if shape_str == "sphere":
                shape = "sphere"
                radius = int(area_match.group(1))
            elif shape_str == "cube":
                shape = "cube"
                size = int(area_match.group(1))
            elif shape_str == "line":
                shape = "line"
                width = int(area_match.group(2))
                length = int(area_match.group(3))
            elif shape_str == "cone":
                shape = "cone"
                width = int(area_match.group(2))
                angle = int(area_match.group(3))
            elif shape_str == "cylinder":
                shape = "cylinder"
                height = int(area_match.group(2))
                radius = int(area_match.group(3))

            area = AreaShape(
                shape=shape,
                radius=radius,
                size=size,
                length=length,
                width=width,
                height=height,
                angle=angle
            )
        return Targeting(type=targeting_type, filters=filters, count=count, selectable=True, area=area)

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

    def _parse_effects(self, text: str) -> List[Effect]:
        lowered: str = text.lower().strip()
        effects: List[Effect] = []

        trigger: Optional[Literal[
            "on_hit", "on_miss",
            "on_save_fail", "on_save_success",
            "on_cast", "on_turn_start", "on_turn_end", "on_enter"
        ]] = None

        if re.search(r"\bmust succeed on\b", lowered, re.IGNORECASE):
            trigger = "on_save_success"
        elif re.search(r"\b(must make|makes|is forced to make)\b.*?saving throw", lowered, re.IGNORECASE):
            trigger = "on_save_fail"
        elif "as you hit" in lowered or "when you hit" in lowered:
            trigger = "on_hit"
        elif "when you cast" in lowered:
            trigger = "on_cast"
        elif "at the start of" in lowered:
            trigger = "on_turn_start"
        elif "enters the area" in lowered or "enters the emanation" in lowered:
            trigger = "on_enter"

        # Condition-Erkennung
        condition_keywords: List[str] = [
            "blinded", "charmed", "deafened", "frightened", "grappled", "incapacitated",
            "paralyzed", "petrified", "poisoned", "restrained", "stunned", "unconscious",
            "invisible", "prone", "exhaustion", "cursed"
        ]

        for keyword in condition_keywords:
            if re.search(rf"\b{keyword}\b", lowered, re.IGNORECASE):
                duration_type: Optional[str] = None
                max_duration: Optional[str] = None
                if "until the start of your next turn" in lowered:
                    duration_type = "timed"
                    max_duration = "start of next turn"
                elif "for the duration" in lowered:
                    duration_type = "timed"

                effects.append(Effect(
                    trigger=trigger,
                    type="condition",
                    condition=ConditionEffect(
                        name=keyword,
                        duration=Duration(type=duration_type, max_duration=max_duration),
                        end_condition=None,
                        stacking="replace"
                    )
                ))

        # Damage-Erkennung
        damage_pattern: str = "|".join(self.DAMAGE_TYPES)
        damage_matches: List[tuple[str, str]] = re.findall(
            rf"(\d+d\d+(?: \+ \d+)?)[^\n]*?\b({damage_pattern})\b",
            lowered,
            re.IGNORECASE
        )
        for dice, dmg_type in damage_matches:
            effects.append(Effect(
                trigger=trigger,
                type="damage",
                damage=[DamageInstance(type=dmg_type, dice=dice)]
            ))

        # --- on_hit damage ---
        hit_matches: List[Tuple[str, str]] = re.findall(
            rf"on a hit.*?(\d+d\d+).*?\b({damage_pattern})\b",
            lowered,
            re.IGNORECASE
        )
        for dice, dmg_type in hit_matches:
            effects.append(Effect(
                trigger="on_hit",
                type="damage",
                damage=[DamageInstance(type=dmg_type, dice=dice)]
            ))

        # --- on_turn_start (ongoing) ---
        ongoing_matches: List[Tuple[str, str, str]] = re.findall(
            rf"(\d+d\d+)\s+({damage_pattern}) damage at the (start|end) of",
            lowered,
            re.IGNORECASE
        )
        for dice_str, dmg_type_str, position_str in ongoing_matches:
            trigger: Literal["on_turn_start", "on_turn_end"] = (
                "on_turn_start" if position_str == "start" else "on_turn_end"
            )
            effects.append(Effect(
                trigger=trigger,
                type="damage",
                damage=[DamageInstance(type=dmg_type_str, dice=dice_str)]
            ))

        # --- on_miss (modifier = half) ---
        if re.search(r"on a miss.*?half", lowered, re.IGNORECASE):
            effects.append(Effect(
                trigger="on_miss",
                type="damage",
                copy_from="on_hit",
                modifier="half"
            ))

        # --- on_successful_save (modifier = half) ---
        if re.search(r"half.*?damage.*?successful", lowered, re.IGNORECASE):
            effects.append(Effect(
                trigger="on_save_success",
                type="damage",
                copy_from="on_save_fail",
                modifier="half"
            ))

        return effects

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
            match = re.search(
                rf"(\b{damage_pattern}\b\s?)? (damage|range)? (?:increases by \d+d\d+|doubles)?\s?when you reach levels (\d+) \(([^)]+)\), (\d+) \(([^)]+)\), and (\d+) \(([^)]+)\)",
                lowered)
            values: List[dict[str, int | str]]

            group_map = [
                (int(match.group(3)), match.group(4)),
                (int(match.group(5)), match.group(6)),
                (int(match.group(7)), match.group(8)),
            ]
            if "damage" in (match.group(2) or ""):
                values = [{"level": lvl, "dice": val} for lvl, val in group_map]
            else:
                values = [{"level": lvl, "mod": val} for lvl, val in group_map]
            per_level: dict[str, str | List[dict[str, int | str]]] = {"effect": str(match.group(2)),
                                                                      "damage_type": match.group(1) if match.group(
                                                                          1) else "", "values": values}
            if match:
                return Scaling(
                    mode=mode,
                    base_level=1,
                    per_level=per_level,
                    per_slot=None
                )
        return Scaling(mode=mode, base_level=1, per_level=None, per_slot=None)

    @staticmethod
    def _parse_requirements(text: str) -> Requirements:
        breath: bool = "verbal" in text.lower()
        hands: int = 1 if "somatic" in text.lower() else 0
        return Requirements(breath_required=breath, hands_free=hands)
