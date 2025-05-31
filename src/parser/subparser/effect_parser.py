import re
from dataclasses import asdict
from typing import List, Optional, Literal, Tuple

from src.parser.models.effect_match import EffectMatch
from src.parser.models.spells import Effect, DamageInstance, Duration, ConditionEffect
from src.parser.subparser.effect_builder import EffectBuilder
from src.parser.utils import DAMAGE_TYPES, CONDITIONS


class EffectParser:
    def __init__(self, description: str):
        self.description: str = description
        self.text: str = description.lower().strip()
        self.trigger: str | None = None

    def parse(self) -> List[Effect]:
        matches: List[EffectMatch] = self.extract()
        return self._deduplicate_effects(EffectBuilder.from_matches(matches))

    def extract(self) -> List[EffectMatch]:
        matches: List[EffectMatch] = []

        # Trigger bestimmen – einmal global, optional vererbbar
        self.trigger = self._detect_trigger()

        # Subextraktionen
        matches += self._extract_conditions()
        matches += self._extract_damage()
        matches += self._extract_half_effects()

        # Optional: Trigger vererben, wenn lokal nicht gesetzt
        for match in matches:
            if match.trigger is None:
                match.trigger = self.trigger

        return matches

    def _detect_trigger(self) -> str | None:
        if "must succeed on" in self.text:
            return "on_save_success"
        elif re.search(r"\b(must make|makes|is forced to make)\b.*?saving throw", self.text):
            return "on_save_fail"
        elif "as you hit" in self.text or "on a hit" in self.text or "when you hit" in self.text:
            return "on_hit"
        elif "when you cast" in self.text:
            return "on_cast"
        elif "at the start of" in self.text:
            return "on_turn_start"
        elif "enters the area" in self.text or "enters the emanation" in self.text:
            return "on_enter"
        return None

    def _extract_damage(self) -> List[EffectMatch]:
        matches: List[EffectMatch] = []

        damage_pattern: str = "|".join(DAMAGE_TYPES)

        base_damage: List[str] = re.findall(rf"(\d+d\d+(?: \+ \d+)?)[^\n]*?\b({damage_pattern})\b", self.text)
        for dice, dtype in base_damage:
            matches.append(EffectMatch(
                type="damage",
                trigger=None,
                raw=f"{dice} {dtype} damage",
                parsed={"dice": dice, "type": dtype}
            ))

        # On-hit damage
        on_hit = re.findall(
            rf"on a hit.*?(\d+d\d+).*?\b({damage_pattern})\b",
            self.text
        )
        for dice, dtype in on_hit:
            matches.append(EffectMatch(
                type="damage",
                trigger="on_hit",
                raw=f"{dice} {dtype} damage (on hit)",
                parsed={"dice": dice, "type": dtype}
            ))

        # On-hit damage plus spellcasting ability modifier
        # Need to add mod to List[Effect]
        on_hit_spellcasting = re.findall(
            rf"on a hit.*?\b({damage_pattern})\b.*?(\d+d\d+).*?(spellcasting.*?modifier)",
            self.text
        )
        for dtype, dice, mod in on_hit_spellcasting:
            matches.append(EffectMatch(
                type="damage",
                trigger="on_hit",
                raw=f"{dice} {dtype} damage (plus spellcasting ability modifier)",
                parsed={"dice": dice, "type": dtype, "plus": mod}
            ))

        # Ongoing damage at start/end of turn
        ongoing = re.findall(
            rf"(\d+d\d+)\s+({damage_pattern}) damage at the (start|end) of",
            self.text
        )
        for dice, dtype, when in ongoing:
            trigger: Literal["on_turn_start", "on_turn_end"] = "on_turn_start" if when == "start" else "on_turn_end"
            matches.append(EffectMatch(
                type="damage",
                trigger=trigger,
                raw=f"{dice} {dtype} damage at {when} of turn",
                parsed={"dice": dice, "type": dtype}
            ))

        return matches

    def _extract_conditions(self) -> List[EffectMatch]:
        matches: List[EffectMatch] = []

        for condition in CONDITIONS:
            # \b = Wortgrenze → damit z.B. "frightened" nicht in "unfrightened" matched
            if re.search(rf"\b{condition}\b", self.text):
                matches.append(EffectMatch(
                    type="condition",
                    trigger=None,  # wird ggf. in extract() global ergänzt oder per Kontext
                    raw=condition,
                    parsed={"name": condition}
                ))

        return matches

    def _extract_half_effects(self) -> List[EffectMatch]:
        matches: List[EffectMatch] = []

        # On miss: half of on_hit
        if re.search(r"on a miss.*?half", self.text):
            matches.append(EffectMatch(
                type="damage",
                trigger="on_miss",
                raw="on a miss ... half",
                parsed={"copy_from": "on_hit", "modifier": "half"}
            ))

        # On successful save: half of on_save_fail
        if re.search(r"half.*?damage.*?successful", self.text):
            matches.append(EffectMatch(
                type="damage",
                trigger="on_save_success",
                raw="half damage on successful save",
                parsed={"copy_from": "on_save_fail", "modifier": "half"}
            ))

        return matches

    @staticmethod
    def _deduplicate_effects(effects: List[Effect]) -> List[Effect]:
        duplicates: List[int] = []

        for i, e1 in enumerate(effects):
            d1 = asdict(e1)
            for j, e2 in enumerate(effects[i + 1:], start=i + 1):
                d2 = asdict(e2)

                # gleiche Inhalte
                d1_no_trigger = {k: v for k, v in d1.items()}
                d2_no_trigger = {k: v for k, v in d2.items()}

                if d1_no_trigger == d2_no_trigger:
                    duplicates.append(i)

        # Entferne Duplikate rückwärts
        for index in sorted(set(duplicates), reverse=True):
            effects.pop(index)

        return effects
