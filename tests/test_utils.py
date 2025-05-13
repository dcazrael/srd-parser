# tests/test_utils.py
from pathlib import Path
import json
from typing import Any

from parser.spell_parser import SpellParser
from parser.models.spells import Spell

def load_md(name: str) -> str:
    path = Path(__file__).parent / "data" / name
    return path.read_text(encoding="utf-8")

def load_json(name: str) -> dict[str, Any]:
    path = Path(__file__).parent / "data" / name
    return json.loads(path.read_text(encoding="utf-8"))

def formatted_spell_name(name: str) -> str:
    return name.lower().replace(" ", "_")

def load_spell(filename: str, amount: int = 1) -> Spell:
    md: str = load_md(filename)
    parser: SpellParser = SpellParser(md)
    parser.parse()
    assert len(parser.spells) == amount
    return parser.spells[0]
