from src.parser.models.spells import Requirements
from src.parser.subparser.base_parser import TextParserBase


class RequirementsParser(TextParserBase):
    def parse(self) -> Requirements:
        breath: bool = "verbal" in self.text
        hands: int = 1 if "somatic" in self.text else 0
        return Requirements(breath_required=breath, hands_free=hands)
