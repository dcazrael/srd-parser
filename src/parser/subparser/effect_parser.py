import re
from dataclasses import asdict
from typing import List, Optional, Literal, Tuple

from src.parser.models.spells import Effect, DamageInstance, Duration, ConditionEffect


class EffectParser:
    def __init__(self, description: str):
        self.description: str = description
        self.DAMAGE_TYPES: List[str] = [
            "base", "initial", "acid", "fire", "cold", "lightning", "radiant", "necrotic",
            "force", "thunder", "psychic", "poison", "bludgeoning", "piercing", "slashing"
        ]

    def parse(self):
        lowered: str = self.description.lower().strip()
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

        return self._deduplicate_effects(effects)

    def _extract_damage(self, text: str) -> Optional[Effect]:
        pass

    def _extract_conditions(self, text: str) -> Optional[Effect]:
        pass

    def _extract_half_effects(self, text: str) -> Optional[Effect]:
        pass

    @staticmethod
    def _deduplicate_effects(effects: List[Effect]) -> List[Effect]:
        duplicates: List[int] = []

        for i, e1 in enumerate(effects):
            d1 = asdict(e1)
            for j, e2 in enumerate(effects[i + 1:], start=i + 1):
                d2 = asdict(e2)

                # gleiche Inhalte außer trigger
                d1_no_trigger = {k: v for k, v in d1.items() if k != "trigger"}
                d2_no_trigger = {k: v for k, v in d2.items() if k != "trigger"}

                if d1_no_trigger == d2_no_trigger:
                    # Nur den triggerlosen Effekt entfernen
                    if d1["trigger"] is None:
                        duplicates.append(i)
                    elif d2["trigger"] is None:
                        duplicates.append(j)

        # Entferne Duplikate rückwärts
        for index in sorted(set(duplicates), reverse=True):
            effects.pop(index)

        return effects