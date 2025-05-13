import argparse
import json
from dataclasses import asdict
from parser.old_spell_parser import SpellParser

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", "-i", required=True, help="Path to input .md file")
    parser.add_argument("--outfile", "-o", required=True, help="Path to output .json file")
    args = parser.parse_args()

    with open(args.infile, encoding="utf-8") as f:
        raw_text = f.read()

    extractor = SpellParser(raw_text)
    extractor.parse()

    extended_spells = [asdict(postprocess_spell(s)) for s in extractor.spells]

    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(extended_spells, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    cli()
