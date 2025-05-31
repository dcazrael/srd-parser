from typing import List

from src.parser.models.effect_match import EffectMatch
from src.parser.models.spells import Effect, DamageInstance, ConditionEffect, Duration


class EffectBuilder:
    @staticmethod
    def from_matches(matches: List[EffectMatch]) -> List[Effect]:
        effects: List[Effect] = []

        for match in matches:
            match_type = match.type
            trigger = match.trigger

            if match_type == "damage":
                if "dice" in match.parsed and "type" in match.parsed:
                    effects.append(Effect(
                        type="damage",
                        trigger=trigger,
                        damage=[DamageInstance(
                            type=match.parsed["type"],
                            dice=match.parsed["dice"]
                        )]
                    ))
                elif "copy_from" in match.parsed and "modifier" in match.parsed:
                    effects.append(Effect(
                        type="damage",
                        trigger=trigger,
                        copy_from=match.parsed["copy_from"],
                        modifier=match.parsed["modifier"]
                    ))

            elif match_type == "condition":
                cond_name = match.parsed.get("name")
                if cond_name:
                    effects.append(Effect(
                        type="condition",
                        trigger=trigger,
                        condition=ConditionEffect(
                            name=cond_name,
                            duration=Duration(type="special")
                        )
                    ))

        return effects
