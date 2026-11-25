#!/usr/bin/env python3
"""Install roster data for the implemented Reedwake species."""
import json
import re
import sys
from pathlib import Path

roster_path = Path(sys.argv[1])
source = Path(sys.argv[2])
roster = json.loads(roster_path.read_text(encoding="utf-8"))
by_name = {entry["name"]: entry for entry in roster["species"]}

# Keep the starter and first wild species in their existing encounter slots.
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
    "Peathare": "POOCHYENA",
    "Bogrel": "MIGHTYENA",
    "Mirehart": "ABSOL",
    "Siltstilt": "ZIGZAGOON",
    "Reedrake": "LINOONE",
    "Fenstilt": "SKARMORY",
    "Podtick": "WURMPLE",
    "Silkettle": "SILCOON",
    "Latchwing": "BEAUTIFLY",
    "Siltmole": "GEODUDE",
    "Gategrub": "GRAVELER",
    "Lockmole": "GOLEM",
    "Sporelet": "SHROOMISH",
    "Budwing": "BRELOOM",
    "Graftwing": "HERACROSS",
    "Gullit": "TAILLOW",
    "Vaneagle": "SWELLOW",
    "Galegull": "TROPIUS",
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
    if entry["familyId"] in (4, 5, 6):
        block = set_field(block, "growthRate", "GROWTH_MEDIUM_FAST")
    elif entry["family"] == "Graftwing":
        block = set_field(block, "growthRate", "GROWTH_FLUCTUATING")
    elif entry["family"] == "Galegull":
        block = set_field(block, "growthRate", "GROWTH_MEDIUM_SLOW")
    info = info[:match.start()] + block + info[match.end():]

    name_pattern = re.compile(rf'(?m)^(\s*\[SPECIES_{slot}\]\s*=\s*)_\("[^"]*"\)(,)')
    names, count = name_pattern.subn(lambda m: m.group(1) + '_("%s")' % name.upper() + m.group(2), names, count=1)
    if count != 1:
        raise SystemExit(f"Could not rename source species slot {slot}")

dex_entries_path = source / "src/data/pokemon/pokedex_entries.h"
dex_text_path = source / "src/data/pokemon/pokedex_text.h"
learnsets_path = source / "src/data/pokemon/level_up_learnsets.h"
evolution_path = source / "src/data/pokemon/evolution.h"
learnset_pointers_path = source / "src/data/pokemon/level_up_learnset_pointers.h"
field_entries = json.loads(roster_path.with_name("field_entries.json").read_text(encoding="utf-8"))
dex_entries = dex_entries_path.read_text(encoding="utf-8")
dex_text = dex_text_path.read_text(encoding="utf-8")
learnsets = learnsets_path.read_text(encoding="utf-8")
evolution_table = evolution_path.read_text(encoding="utf-8")
learnset_pointers = learnset_pointers_path.read_text(encoding="utf-8")

for name, slot in slots.items():
    entry = field_entries[name]

    category = entry["category"]
    if len(category) > 11:
        raise SystemExit(f"Pokédex category for {name} exceeds 11 characters")
    dex_pattern = re.compile(rf"(?ms)^    \[NATIONAL_DEX_{slot}\] =\n    \{{.*?^    \}},")
    match = dex_pattern.search(dex_entries)
    if match is None:
        raise SystemExit(f"Missing Pokédex entry for {name}")
    block = match[0]
    description = re.search(r"\.description = (\w+),", block)
    if description is None:
        raise SystemExit(f"Missing Pokédex description pointer for {name}")
    for field, value in (
        ("categoryName", f'_("{category}")'),
        ("height", str(entry["heightDm"])),
        ("weight", str(entry["weightHg"])),
    ):
        block = set_field(block, field, value)
    dex_entries = dex_entries[:match.start()] + block + dex_entries[match.end():]

    symbol = description.group(1)
    replacement = f"const u8 {symbol}[] = _(\n"
    replacement += "\n".join("    " + json.dumps(line + ("\n" if i < len(entry["text"]) - 1 else ""),
                                               ensure_ascii=False)
                             for i, line in enumerate(entry["text"]))
    replacement += ");"
    dex_text, count = re.subn(rf"(?ms)^const u8 {symbol}\[\] = _\(.*?\);",
                              lambda _: replacement, dex_text, count=1)
    if count != 1:
        raise SystemExit(f"Missing Pokédex text for {name}")

    if "levelUp" in entry:
        pointer = re.search(rf"(?m)^    \[SPECIES_{slot}\] = (\w+),$", learnset_pointers)
        if pointer is None:
            raise SystemExit(f"Missing learnset pointer for {name}")
        symbol = pointer.group(1)
        replacement = f"static const u16 {symbol}[] = {{\n"
        for level, move in entry["levelUp"]:
            replacement += f"    LEVEL_UP_MOVE({level:2d}, MOVE_{move}),\n"
        replacement += "    LEVEL_UP_END\n};"
        learnsets, count = re.subn(rf"(?ms)^static const u16 {symbol}\[\] = \{{.*?^\}};",
                                   lambda _: replacement, learnsets, count=1)
        if count != 1:
            raise SystemExit(f"Missing learnset definition for {name}")

    target = by_name[name]["evolvesTo"]
    if target:
        evolution = f"    [SPECIES_{slot}] = {{{{EVO_LEVEL, {by_name[name]['evolvesAt']}, SPECIES_{slots[target]}}}}},"
        evolution_pattern = re.compile(rf"(?ms)^    \[SPECIES_{slot}\]\s*=\s*\{{\{{.*?\}}\}},")
        existing = evolution_pattern.search(evolution_table)
        if existing is not None:
            evolution_table = evolution_table[:existing.start()] + evolution + evolution_table[existing.end():]
        else:
            marker = "const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] =\n{"
            evolution_table = evolution_table.replace(marker, marker + "\n" + evolution, 1)

dex_entries_path.write_text(dex_entries, encoding="utf-8")
dex_text_path.write_text(dex_text, encoding="utf-8")
learnsets_path.write_text(learnsets, encoding="utf-8")
evolution_path.write_text(evolution_table, encoding="utf-8")
info_path.write_text(info, encoding="utf-8")
names_path.write_text(names, encoding="utf-8")
