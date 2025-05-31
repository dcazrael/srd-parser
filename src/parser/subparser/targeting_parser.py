import re
from typing import Optional, List, Literal, cast

from src.parser.models.spells import Targeting, AreaShape
from src.parser.utils import word_to_number


class TargetingParser:
    def __init__(self, text: str):
        self.text = text.lower().strip()

    def parse(self) ->Targeting:
        targeting_type: str = "creature"
        filters: Optional[List[str]] = []
        count: Optional[int] = None
        selectable: bool = True
        area: Optional[AreaShape] = None

        shape_str: str

        if "self" in self.text:
            targeting_type = "self"

        # Touch-based
        if "you touch" in self.text:
            targeting_type = "touch"
            count = 1
            return Targeting(type=targeting_type, filters=[], count=count, selectable=True, area=None)

        # "target you can see within range"
        if re.search(r"target (a|one)? \w+ that you can see within range", self.text):
            count = 1
            filters.append("you can see")

        # "one creature", "two targets", etc.
        match = re.search(
            r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b (creature|target|humanoid|beast)s?",
            self.text)
        if match:
            word = match.group(1)
            count = int(word) if word.isdigit() else word_to_number(word)

        # "up to X creatures"
        match = re.search(r"up to (\d+) (willing )?(creature|target|humanoid|beast)s?", self.text)
        if match:
            count = int(match.group(1))
            if match.group(2):
                filters.append("willing")

        # "any number of willing creatures"
        if "any number of willing" in self.text:
            count = None
            filters.append("willing")

        area_match: Optional[re.Match] = re.search(
            r"(\d+)-foot(?:-tall,)? (\d+)-foot(?:-radius)? (sphere|cube|cone|cylinder|circle)", self.text,
            re.IGNORECASE)

        line_pattern = re.compile(
            r"(?P<length>\d+)[ -]?foot(?:-long)?\W+(?P<width>\d+)[ -]?foot(?:-wide)?\W+line"
            r"|(?P<width_alt>\d+)[ -]?foot(?:-wide)?\W+(?P<length_alt>\d+)[ -]?foot(?:-long)?\W+line",
            re.IGNORECASE
        )
        line_match:Optional[re.Match] = line_pattern.search(self.text)

        if area_match:
            selectable = "of your choice" in self.text or "you choose" in self.text
            count = None
            targeting_type = "area"
            shape: Literal["sphere", "cube", "line", "cone", "cylinder", "circle"] = cast(Literal["sphere", "cube", "line", "cone", "cylinder", "circle"], area_match.group(3))
            size = int(area_match.group(2))

            if shape in {"sphere", "circle"}:
                area = AreaShape(shape=shape, radius=size)
            elif shape == "cube":
                area = AreaShape(shape=shape, size=size)
            elif shape == "cone":
                area = AreaShape(shape=shape, length=size)
            elif shape == "cylinder":
                height = int(area_match.group(1))
                area = AreaShape(shape=shape, length=size, height=height)
        elif line_match:
            targeting_type = "area"
            length = int(line_match.group("length") or line_match.group("length_alt"))
            width = int(line_match.group("width") or line_match.group("width_alt"))
            area = AreaShape(shape="line", length=length, width=width)
            selectable = False
            count = None

        return Targeting(type=targeting_type, filters=filters or None, count=count, selectable=selectable, area=area)
