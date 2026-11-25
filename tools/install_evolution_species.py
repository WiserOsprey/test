#!/usr/bin/env python3
"""Install roster stats, abilities, and names for Reedwake's starters."""
import json
import re
import sys
from pathlib import Path

roster_path = Path(sys.argv[1])
source = Path(sys.argv[2])
roster = json.loads(roster_path.read_text(encoding="utf-8"))
by_name = {entry["name"]: entry for entry in roster["species"]}

# Reedwake's starters use the three Hoenn starter lines.
slots = {
    "Fernut": "TREECKO",
    "Cindrix": "TORCHIC",
    "Rillfin": "MUDKIP",
    "Bramblet": "GROVYLE",
    "Canoplate": "SCEPTILE",
    "Flareden": "COMBUSKEN",
    "Vulprism": "BLAZIKEN",
    "Bendruff": "MARSHTOMP",
    "Estuarch": "SWAMPERT",
}
type_ids = {
    "Normal": "NORMAL", "Fire": "FIRE", "Water": "WATER", "Electric": "ELECTRIC",
    "Grass": "GRASS", "Ice": "ICE", "Fighting": "FIGHTING", "Poison": "POISON",
    "Ground": "GROUND", "Flying": "FLYING", "Psychic": "PSYCHIC", "Bug": "BUG",
    "Rock": "ROCK", "Ghost": "GHOST", "Dragon": "DRAGON", "Dark": "DARK",
    "Steel": "STEEL",
}
colors = {
    "Fire": "RED", "Water": "BLUE", "Electric": "YELLOW", "Grass": "GREEN",
    "Ice": "WHITE", "Fighting": "BROWN", "Poison": "PURPLE", "Ground": "BROWN",
    "Flying": "BLUE", "Psychic": "PINK", "Bug": "GREEN", "Rock": "BROWN",
    "Ghost": "BLACK", "Dragon": "GREEN", "Dark": "BLACK", "Steel": "GRAY",
    "Normal": "BROWN",
}

info_path = source / "src/data/pokemon/species_info.h"
names_path = source / "src/data/text/species_names.h"
info = info_path.read_text(encoding="utf-8")
names = names_path.read_text(encoding="utf-8")

def set_field(block, field, value):
    pattern = rf"(?m)^(\s*\.{re.escape(field)}\s*=\s*).*$"
    result, count = re.subn(pattern, lambda m: m.group(1) + value + ",", block, count=1)
    if count != 1:
        raise SystemExit(f"Could not update {field} in species info")
    return result

for name, slot in slots.items():
    entry = by_name[name]
    pattern = re.compile(rf"(?ms)^    \[SPECIES_{slot}\] =\n    \{{.*?^    \}},")
    match = pattern.search(info)
    if match is None:
        raise SystemExit(f"Could not find source species slot {slot}")
    block = match.group(0)
    stats = entry["stats"]
    values = {
        "baseHP": stats["hp"],
        "baseAttack": stats["attack"],
        "baseDefense": stats["defense"],
        "baseSpeed": stats["speed"],
        "baseSpAttack": stats["specialAttack"],
        "baseSpDefense": stats["specialDefense"],
    }
    for field, value in values.items():
        block = set_field(block, field, str(value))
    type_names = entry["types"]
    type_a = type_ids[type_names[0]]
    type_b = type_ids[type_names[1]] if len(type_names) > 1 else type_a
    block = set_field(block, "types", "{ TYPE_%s, TYPE_%s }" % (type_a, type_b))
    ability = entry["ability"].upper().replace(" ", "_")
    block = set_field(block, "abilities", "{ABILITY_%s, ABILITY_NONE}" % ability)
    body_color = colors[type_names[0]]
    block = set_field(block, "bodyColor", "BODY_COLOR_%s" % body_color)
    info = info[:match.start()] + block + info[match.end():]

    name_pattern = re.compile(rf'(?m)^(\s*\[SPECIES_{slot}\]\s*=\s*)_\("[^"]*"\)(,)')
    names, count = name_pattern.subn(lambda m: m.group(1) + '_("%s")' % name.upper() + m.group(2), names, count=1)
    if count != 1:
        raise SystemExit(f"Could not rename source species slot {slot}")

info_path.write_text(info, encoding="utf-8")
names_path.write_text(names, encoding="utf-8")
