def assert_spell_matches(spell, expected: dict):
    assert spell.name == expected["name"], f"❌ Name: {spell.name} ≠ {expected['name']}"
    assert spell.level == expected["level"], f"❌ Level: {spell.level} ≠ {expected['level']}"
    assert spell.school == expected["school"], f"❌ School: {spell.school} ≠ {expected['school']}"
    assert spell.classes == expected["classes"], f"❌ Classes: {spell.classes} ≠ {expected['classes']}"
    assert spell.casting_time == expected["casting_time"], f"❌ Casting Time: {spell.casting_time} ≠ {expected['casting_time']}"
    assert spell.range == expected["range"], f"❌ Range: {spell.range} ≠ {expected['range']}"
    assert spell.components == expected["components"], f"❌ Components: {spell.components} ≠ {expected['components']}"
    assert spell.duration == expected["duration"], f"❌ Duration: {spell.duration} ≠ {expected['duration']}"
    assert spell.description.startswith(expected["description_startswith"]), "❌ Beschreibung nicht wie erwartet"
    assert expected["higher_levels"] in spell.higher_levels, "❌ higher_levels nicht enthalten"

    if "description_contains" in expected:
        for fragment in expected["description_contains"]:
            assert fragment in spell.description, f"❌ '{fragment}' fehlt in Beschreibung"

    if "subsections" in expected:
        assert len(spell.subsections) == len(expected["subsections"]), f"❌ Anzahl subsections falsch: {len(spell.subsections)}"
        for i, sub in enumerate(spell.subsections):
            assert sub.name == expected["subsections"][i]["name"], f"❌ subsection {i} name: {sub.name}"
            assert sub.content.startswith(expected["subsections"][i]["content_startswith"]), f"❌ subsection {i} content falsch"
            assert sub.type == expected["subsections"][i]["type"], f"❌ subsection {i} type falsch: {sub.type}"
