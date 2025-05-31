from dataclasses import dataclass
from typing import Optional, List, Literal

# --- Zauber-Komponenten ---
@dataclass
class CastingTime:
    type: str|List[str]  # "action", "bonus_action", "reaction", ["minute","ritual"]
    cost: int

@dataclass
class ComponentMaterial:
    required: bool
    consumed: bool
    description: Optional[str] = None
    value_gp: Optional[float] = None

@dataclass
class Components:
    verbal: bool
    somatic: bool
    material: Optional[ComponentMaterial] = None

# --- Zauberbereich & Reichweite ---
@dataclass
class SpellRange:
    type: str  # "point", "self", "touch"
    distance: Optional[str] = None

# --- Dauer ---
@dataclass
class Duration:
    type: str  # "instantaneous", "concentration", etc.
    max_duration: Optional[str] = None

# --- Rettungswürfe & Skalierung ---
@dataclass
class SaveInfo:
    type: Literal["str", "dex", "con", "int", "wis", "cha"]
    dc_source: Literal["spellcasting", "custom"]
    negates: bool

@dataclass
class Scaling:
    mode: Literal["slot_level", "level_threshold"]
    base_level: int
    per_level: Optional[dict]  # {"effect": ..., "value": ...}
    per_slot: Optional[dict]  # {"effect": ..., "value": ...}

# --- Anforderungen & Constraints ---
@dataclass
class Requirements:
    breath_required: bool
    hands_free: int
    focus_available: Optional[bool] = True

# --- End-Bedingungen für Zustände ---
@dataclass
class EndCondition:
    type: Literal["saving_throw"]
    ability: str
    frequency: Literal["start_of_turn", "end_of_turn", "once"]
    success_ends: bool

# --- Effekt bei Bedingungen ---
@dataclass
class ConditionEffect:
    name: str
    duration: Duration
    end_condition: Optional[EndCondition] = None  # E.g. "end_of_turn_save"
    stacking: Literal["replace", "ignore", "extend"] = "replace"

@dataclass
class DamageInstance:
    type: str  # e.g. "fire"
    dice: str  # e.g. "8d6"

@dataclass
class Effect:
    type: Literal["damage", "condition", "heal", "summon", "teleport"]
    trigger: Literal[
        "on_hit", "on_miss",
        "on_save_fail", "on_save_success",
        "on_cast", "on_turn_start", "on_turn_end", "on_enter"
    ]|None = None
    damage: Optional[List[DamageInstance]] = None
    condition: Optional[ConditionEffect] = None
    copy_from: Optional[str] = None
    modifier: Optional[str] = None  # e.g. "half"

@dataclass
class Resolution:
    type: Literal["saving_throw", "attack_roll", "automatic"]
    save_type: Optional[Literal["str", "dex", "con", "int", "wis", "cha"]] = None

# --- Zielmechanik und Filter ---
@dataclass
class AreaShape:
    shape: Literal["sphere", "cube", "line", "cone", "cylinder", "circle"]
    size: Optional[int] = None  # für cube: edge length, sphere: diameter oder radius
    length: Optional[int] = None  # für line, cone
    width: Optional[int] = None  # für line
    radius: Optional[int] = None  # für sphere, cylinder, circle
    height: Optional[int] = None  # für cylinder

@dataclass
class Targeting:
    type: str  # "creature", "area", ...
    filters: Optional[List[str]] = None  # z.B. "humanoid", "enemy"
    count: Optional[int] = None
    selectable: Optional[bool] = True
    area: Optional[AreaShape] = None

# --- Haupt-Zauber-Modell ---
@dataclass
class Subsection:
    name: str
    text: str

@dataclass
class Spell:
    name: str
    level: int
    school: str
    classes: List[str]
    casting_time: CastingTime
    components: Components
    range: SpellRange
    duration: Duration
    targeting: Targeting
    effects: List[Effect]
    description: str
    save: Optional[SaveInfo] = None
    scaling: Optional[Scaling] = None
    requirements: Optional[Requirements] = None
    resolution: Optional[Resolution] = None
    subsections: Optional[List[Subsection]] = None
    tags: Optional[List[str]] = None  # z.B. "fire", "concentration"
