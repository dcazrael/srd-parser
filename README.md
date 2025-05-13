# D&D 5e SRD Markdown Parser

Ein modularer, TDD-getriebener Parser für Dungeons & Dragons 5e System Reference Document (SRD)-Daten im Markdown-Format. Ziel ist die strukturierte Umwandlung in JSON, das sich sowohl für AI-gestützte Spielsysteme (z. B. SoloQuest) als auch für Regelanzeigen, Tooltips und automatische Entscheidungen eignet.

## 📦 Features

- Vollständige Spell-Extraktion aus Markdown-Dateien
- Unterstützung für:
  - Komponenten, Material, Casting Time
  - Scaling (Slot- & Level-basiert)
  - Effekte (Damage, Conditions, Healing, etc.)
  - Resolution & Trigger (z. B. on_hit, on_save_fail)
  - Targeting inklusive AreaShape
  - Subsections (z. B. Audible Alarm / Mental Alarm)
- Modulares Datenmodell mit vollständiger Typisierung (`@dataclass`)
- Vollständige TDD-Testabdeckung pro Spell
- Markdown bleibt die einzige Quelle (kein manuelles Mapping)

## 🧠 Verwendete Technologien

- Python 3.11+
- `dataclasses`, `re`, `typing`
- `pytest` für testgetriebene Validierung
- keine externen Parser- oder Frontend-Abhängigkeiten

## 🗂️ Projektstruktur

```text
src/
  parser/
    spell_parser.py         # Hauptparser
    models/                 # Strukturierte Datamodelle
    postprocess.py          # Optionale Zusatztransformationen
tests/
  test_spell_parser.py      # Einzeltests pro Spell
  test_utils.py             # Loader & Helfer
```

## ▶️ Nutzung

```bash
uv venv
source .venv/bin/activate  # oder .venv\Scripts\activate unter Windows
uv pip install pytest
pytest
```

### Optional: Anforderungen als Datei exportieren

```bash
uv pip freeze > requirements.txt
```

## 🧩 Parser-Strategie

- **Pattern-basiert** mit `re.search`, nicht AI-heuristisch
- Jeder Abschnitt (`**Casting Time**`, `**Range**`, ...) wird einzeln erkannt
- Subsections (`**Titel**.`) werden getrennt gesammelt
- Skalierung (per_slot, per_level) über klare Muster:
  - `"The damage increases by 1d8 for each spell slot level above 3"`
  - `"Cantrip Upgrade. ... levels 5 (2d6), 11 (3d6), 17 (4d6)"`

## 🔄 Beispielausgabe

```json
{
  "name": "Fireball",
  "level": 3,
  "school": "Evocation",
  "components": ["V", "S", "M"],
  "material": "a tiny ball of bat guano",
  "casting_time": { "type": "action", "cost": 1 },
  "range": { "type": "point", "distance": "150 feet" },
  "duration": { "type": "instantaneous" },
  "scaling": { "mode": "slot_level", "base_level": 3, "per_slot": { "effect": "damage", "value": "1d6" }},
  "resolution": { "type": "saving_throw", "save_type": "dex" },
  "effects": [
    { "trigger": "on_save_fail", "type": "damage", "damage": [{ "type": "fire", "dice": "8d6" }] },
    { "trigger": "on_save_success", "type": "damage", "copy_from": "on_save_fail", "modifier": "half" }
  ],
  "targeting": {
    "type": "area",
    "area": { "shape": "sphere", "radius": 20 }
  }
}
```

## 🔧 Geplante Erweiterungen

- Parsing weiterer SRD-Komponenten (Classes, Features, Items)
- Fehlererkennung bei fehlenden Feldern
- Markdown-Validator zur Vorprüfung

## 📜 Lizenz

MIT License – frei nutzbar, solange du deinen eigenen Fireball nicht in der Küche castest.
