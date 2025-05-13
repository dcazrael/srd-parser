# scripts/spell_classifier.py
import csv
from parser.old_spell_parser import SpellParser
from pathlib import Path

def classify_spell(text: str, name: str, level: int) -> dict:
    text_l = text.lower()
    return {
        "name": name,
        "level": level,
        "has_spell_attack": "make a ranged spell attack" in text_l or "make a melee spell attack" in text_l,
        "has_save": "saving throw" in text_l,
        "has_ongoing": "at the end of its next turn" in text_l,
        "has_condition": "condition" in text_l or "is " in text_l,
        "has_area": "radius" in text_l or "cone" in text_l or "line" in text_l,
        "has_repeatable": "on each of your turns" in text_l or "again on later turns" in text_l,
        "has_concentration": "concentration" in text_l,
    }

def run():
    md_path = Path("examples/spell_descriptions.md")  # ← muss angepasst werden falls anderer Pfad
    if not md_path.exists():
        raise FileNotFoundError(f"{md_path} nicht gefunden")

    raw_text = md_path.read_text(encoding="utf-8")
    parser = SpellParser(raw_text)
    parser.parse()

    rows = []
    for spell in parser.spells:
        row = classify_spell(spell.description, spell.name, spell.level)
        rows.append(row)

    out_path = Path("tests/data/spell_features.csv")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} spells to {out_path}")

if __name__ == "__main__":
    run()
