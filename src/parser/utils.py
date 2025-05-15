from typing import List

DAMAGE_TYPES: List[str] = [
            "base", "initial", "acid", "fire", "cold", "lightning", "radiant", "necrotic",
            "force", "thunder", "psychic", "poison", "bludgeoning", "piercing", "slashing"
        ]

CONDITIONS: List[str] = [
            "blinded", "charmed", "deafened", "frightened", "grappled", "incapacitated",
            "paralyzed", "petrified", "poisoned", "restrained", "stunned", "unconscious",
            "invisible", "prone", "exhaustion", "cursed"
        ]

TARGETS: List[str] = ["creature", "humanoid", "beast"]


def word_to_number(word: str) -> int:
    table = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return table.get(word.lower(), 1)