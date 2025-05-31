from dataclasses import dataclass
from typing import Literal, Optional, Dict


@dataclass
class EffectMatch:
    type: Literal["damage", "condition"]
    trigger: Optional[Literal[
        "on_hit", "on_miss", "on_save_fail", "on_save_success", "on_cast", "on_turn_start", "on_turn_end", "on_enter"
    ]]
    raw: str
    parsed: Dict[str, str]
