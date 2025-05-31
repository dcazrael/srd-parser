import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any

import yaml

from src.parser.spell_parser import SpellParser
from src.parser.utils import slugify


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", "-i", required=True, help="Path to input .md file")
    args = parser.parse_args()

    with open(args.infile, encoding="utf-8") as f:
        raw_text = f.read()

    extractor = SpellParser(raw_text)
    extractor.parse()

    for spell in extractor.spells:
        spell_dict: Dict[str, Any] = asdict(spell)
        level_dir: Path = Path("output/data/spells") / f"level_{spell.level}"
        level_dir.mkdir(parents=True, exist_ok=True)

        file_path = level_dir / f"{slugify(spell.name)}.yaml"

        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(spell_dict, f, allow_unicode=True, sort_keys=False, indent=4)

        print(f"Spell exportiert: {file_path}")


if __name__ == "__main__":
    cli()
