import re
from typing import List, Dict, Any, Optional

from .block_segmenter import BlockSegmenter
from .models.spells import Components, CastingTime, Effect, Duration, \
    Requirements, SpellRange, Spell, Scaling, SaveInfo, Targeting, Subsection
from .subparser.effect_parser import EffectParser
from .subparser.requirements_parser import RequirementsParser
from .subparser.resolution_parser import ResolutionParser
from .subparser.save_parser import SaveParser
from .subparser.scaling_parser import ScalingParser
from .subparser.section_parser import SectionParser
from .subparser.spell_info_parser import SpellInfoParser
from .subparser.targeting_parser import TargetingParser


class SpellParser:
    def __init__(self, text: str):
        self.text: str = text
        self.spells: List[Spell] = []

        self.DAMAGE_TYPES: List[str] = [
            "base", "initial", "acid", "fire", "cold", "lightning", "radiant", "necrotic",
            "force", "thunder", "psychic", "poison", "bludgeoning", "piercing", "slashing"
        ]

    def parse(self):
        start: int = self.text.find("#### ")
        if start == -1:
            self.text = self.text[start:]

        raw_blocks: List[str] = re.split(r"^#### (.+)", self.text, flags=re.MULTILINE)
        for i in range(1, len(raw_blocks), 2):
            name: str = raw_blocks[i].strip()
            body: str = raw_blocks[i + 1]

            header_lines: List[str]
            description_block: str
            subsection_blocks: List[str]
            header_lines, description_block, subsection_blocks = BlockSegmenter(body).extract()
            spell: Spell = self.parse_single_spell(name, header_lines, description_block, subsection_blocks)
            self.spells.append(spell)

    @staticmethod
    def parse_single_spell(name: str, header_lines: List[str], description: str, subsection_blocks: List[str]) -> Spell:
        meta_line: str = header_lines[0]
        level: int
        school: str
        classes: List[str]
        level, school, classes = SpellInfoParser.parse_metadata(meta_line)

        sections: Dict[str, Any] = SectionParser(header_lines[1:], subsection_blocks).parse()

        casting_time: CastingTime = SpellInfoParser.parse_casting_time(sections.get("Casting Time", ""))
        components: Components = SpellInfoParser.parse_components(sections.get("Components", ""))
        spell_range: SpellRange = SpellInfoParser.parse_spell_range(sections.get("Range", ""))
        duration: Duration = SpellInfoParser.parse_duration(sections.get("Duration", ""))
        effects: List[Effect] = EffectParser(description).parse()
        targeting: Targeting = TargetingParser(description).parse()
        save: Optional[SaveInfo] = SaveParser(description).parse()
        subsections: List[Subsection] = sections.get("subsections", [])
        scaling: Optional[Scaling] = ScalingParser(subsections).parse()
        requirements: Optional[Requirements] = RequirementsParser(description).parse()
        resolution = ResolutionParser(description).parse()

        return Spell(
            name=name,
            level=level,
            school=school,
            classes=classes,
            casting_time=casting_time,
            range=spell_range,
            components=components,
            duration=duration,
            description=description,
            targeting=targeting,
            effects=effects,
            save=save,
            scaling=scaling,
            requirements=requirements,
            resolution=resolution,
            subsections=subsections,
            tags=[]
        )