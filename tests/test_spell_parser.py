import pytest

from src.parser.models.spells import Spell
from tests.test_utils import load_spell, formatted_spell_name

def test_acid_arrow() -> None:
    spell_name: str = formatted_spell_name("Acid Arrow")
    spell: Spell = load_spell(f"{spell_name}.md")

    print(spell)

    assert spell.name == "Acid Arrow"
    assert spell.level == 2
    assert spell.school == "Evocation"
    assert spell.classes == ["Wizard"]

    assert spell.description.startswith("A shimmering green arrow")
    assert "4d4" in spell.description
    assert "2d4" in spell.description

    assert spell.casting_time.type == "action"
    assert spell.casting_time.cost == 1

    assert spell.range.distance == "90 feet"

    assert spell.components.verbal is True
    assert spell.components.somatic is True
    assert spell.components.material is not None
    assert "rhubarb" in (spell.components.material.description or "")

    assert spell.duration.type == "instantaneous"
    assert spell.targeting.type == "creature"

    # Effektprüfungen
    assert len(spell.effects) == 3

    hit = next((e for e in spell.effects if e.trigger == "on_hit"), None)
    assert hit is not None
    assert hit.type == "damage"
    assert any(di.dice == "4d4" and di.type == "acid" for di in hit.damage or [])

    ongoing = next((e for e in spell.effects if e.trigger == "on_turn_end"), None)
    assert ongoing is not None
    assert any(di.dice == "2d4" and di.type == "acid" for di in ongoing.damage or [])

    miss = next((e for e in spell.effects if e.trigger == "on_miss"), None)
    assert miss is not None
    assert miss.copy_from == "on_hit"
    assert miss.modifier == "half"

def test_acid_splash() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Acid Splash')}.md")
    assert spell.name == "Acid Splash"
    assert spell.level == 0
    assert spell.school == "Evocation"
    assert spell.classes == ["Sorcerer", "Wizard"]

    assert spell.description.startswith("You create an acidic bubble")
    assert "1d6" in spell.description
    assert "5-foot-radius" in spell.description

    assert spell.casting_time.type == "action"
    assert spell.casting_time.cost == 1

    assert spell.range.distance == "60 feet"


    assert spell.components.verbal is True
    assert spell.components.somatic is True
    assert spell.components.material is None

    assert spell.duration.type == "instantaneous"
    assert spell.targeting.type == "area"
    assert spell.targeting.area.shape == "sphere"
    assert spell.targeting.area.radius == 5

    # Effektprüfungen
    hit = next((e for e in spell.effects if e.trigger == "on_save_success"), None)
    assert hit is not None
    assert hit.type == "damage"
    assert any(di.dice == "1d6" and di.type == "acid" for di in hit.damage or [])

    assert spell.save.dc_source == "spellcasting"
    assert spell.save.type == "dex"
    assert spell.save.negates == True

    assert spell.scaling.mode == "level_threshold"
    assert spell.scaling.base_level == 1
    assert spell.scaling.per_level == {"effect": "damage", "damage_type": "", "values":[{"level": 5, "dice": "2d6"}, {"level": 11, "dice": "3d6"}, {"level": 17, "dice": "4d6"}]}


def test_alarm() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Alarm')}.md")
    assert spell.name == "Alarm"
    assert spell.level == 1
    assert spell.school == "Abjuration"
    assert spell.classes == ["Ranger", "Wizard"]
    assert "20-foot cube" in spell.description.lower()

    assert spell.casting_time.type == ["minute", "ritual"]
    assert spell.casting_time.cost == 1

    assert spell.range.distance == "30 feet"
    assert spell.components.verbal is True
    assert spell.components.somatic is True
    assert spell.components.material.required is True
    assert spell.components.material.description == "a bell and silver wire"
    assert spell.duration.type == "timed"
    assert spell.duration.max_duration == "8 hours"

    assert spell.targeting.type == "area"
    assert spell.targeting.area.shape == "cube"
    assert spell.targeting.area.size == 20

    assert spell.subsections[0].name == "Audible Alarm"
    assert spell.subsections[0].text.startswith("The alarm produces the sound")

    assert spell.subsections[1].name == "Mental Alarm"
    assert spell.subsections[1].text.startswith("You are alerted by a mental ping")


def test_fireball() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Fireball')}.md")
    assert spell.name == "Fireball"
    assert spell.level == 3
    assert spell.school == "Evocation"
    assert spell.classes == ["Sorcerer", "Wizard"]
    assert "dexterity saving throw" in spell.description.lower()

    assert spell.casting_time.type == "action"
    assert spell.casting_time.cost == 1

    assert spell.range.distance == "150 feet"
    assert spell.components.verbal is True
    assert spell.components.somatic is True
    assert spell.components.material.required is True
    assert spell.components.material.description == "a ball of bat guano and sulfur"
    assert spell.duration.type == "instantaneous"

    assert spell.description.startswith("A bright streak flashes from you to a point you")

    save_fail = next((e for e in spell.effects if e.trigger == "on_save_fail"), None)
    assert save_fail is not None
    assert save_fail.type == "damage"
    assert any(di.dice == "8d6" and di.type == "fire" for di in save_fail.damage or [])

    save_success = next((e for e in spell.effects if e.trigger == "on_save_success"), None)
    assert save_success is not None
    assert save_success.type == "damage"
    assert save_success.copy_from == "on_save_fail"
    assert save_success.modifier == "half"

    assert spell.save.dc_source == "spellcasting"
    assert spell.save.type == "dex"
    assert spell.save.negates == False

    assert spell.scaling.mode == "slot_level"
    assert spell.scaling.base_level == 3

    assert any(e.trigger == "on_save_fail" and e.type == "damage" for e in spell.effects)

def test_flame_blade() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Flame Blade')}.md")
    assert spell.name == "Flame Blade"
    assert spell.level == 2
    assert spell.school == "Evocation"

def test_flame_strike() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Flame Strike')}.md")
    assert spell.name == "Flame Strike"
    assert spell.level == 5
    assert spell.school == "Evocation"

def test_hold_person() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Hold Person')}.md")
    assert spell.name == "Hold Person"
    assert spell.level == 2
    assert spell.school == "Enchantment"
    assert any(e.type == "condition" for e in spell.effects)

def test_magic_missile() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Magic Missile')}.md")
    assert spell.name == "Magic Missile"
    assert spell.level == 1
    assert spell.school == "Evocation"

def test_moonbeam() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Moonbeam')}.md")



    print(repr(spell))
    assert spell.name == "Moonbeam"
    assert spell.level == 2
    assert spell.school == "Evocation"

def test_scorching_ray() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Scorching Ray')}.md")
    assert spell.name == "Scorching Ray"
    assert spell.level == 2
    assert spell.school == "Evocation"

def test_searing_smite() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Searing Smite')}.md")
    assert spell.name == "Searing Smite"
    assert spell.level == 1
    assert spell.school == "Evocation"

def test_shining_smite() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Shining Smite')}.md")
    assert spell.name == "Shining Smite"
    assert spell.level == 2
    assert spell.school == "Transmutation"

def test_vitriolic_sphere() -> None:
    spell: Spell = load_spell(f"{formatted_spell_name('Vitriolic Sphere')}.md")
    assert spell.name == "Vitriolic Sphere"
    assert spell.level == 4
    assert spell.school == "Evocation"
