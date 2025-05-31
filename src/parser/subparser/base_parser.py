from abc import ABC


class TextParserBase(ABC):
    def __init__(self, text: str):
        self.text: str = text.lower().strip()

    def parse(self):
        pass
