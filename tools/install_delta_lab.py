#!/usr/bin/env python3
"""Install Reedwake's permanent starter Delta forms and the field lab."""
import json
import re
import sys
from pathlib import Path

roster_path, source = map(Path, sys.argv[1:3])
roster = json.loads(roster_path.read_text(encoding="utf-8"))
entries = {entry["name"]: entry for entry in roster["species"]}

# These dormant Emerald slots precede the Hoenn species range.
starter_slots = {
    "Fernut": ("TREECKO", "C"),
    "Bramblet": ("GROVYLE", "D"),
    "Canoplate": ("SCEPTILE", "E"),
    "Cindrix": ("TORCHIC", "F"),
    "Flareden": ("COMBUSKEN", "G"),
    "Vulprism": ("BLAZIKEN", "H"),
    "Rillfin": ("MUDKIP", "I"),
    "Bendruff": ("MARSHTOMP", "J"),
    "Estuarch": ("SWAMPERT", "K"),
}
palette_tints = {
    "Electric": ((235, 185, 50), (93, 212, 230)),
    "Ghost": ((167, 106, 221), (112, 214, 192)),
    "Psychic": ((232, 106, 169), (235, 187, 91)),
    "Ice": ((117, 215, 245), (188, 153, 245)),
}
files = {}


def read(path):
    if path not in files:
        files[path] = (source / path).read_text(encoding="utf-8")
    return files[path]


def replace(path, old, new):
    contents = read(path)
    if contents.count(old) != 1:
        raise SystemExit(f"Expected one match in {path}: {old[:130]!r}")
    files[path] = contents.replace(old, new, 1)


def append(path, contents):
    files[path] = read(path).rstrip() + "\n\n" + contents.rstrip() + "\n"


def write_new(path, contents):
    if (source / path).exists() or path in files:
        raise SystemExit(f"File already exists: {path}")
    files[path] = contents


def identifier(label):
    return label.upper().replace(" ", "_")


def clone_row(path, base, dormant, delta):
    contents = read(path)
    for name in (base, dormant):
        pattern = rf"(?m)^    .*?(?:\[SPECIES_{name}\]|,?\({name},).*$"
        matches = re.findall(pattern, contents)
        if len(matches) != 1:
            raise SystemExit(f"Expected one row for {name} in {path}")
        if name == base:
            row = matches[0]
        else:
            replace(path, matches[0], re.sub(rf"\b(SPECIES_)?{base}\b",
                                            lambda m: (m[1] or "") + delta, row))


def make_palette(base, delta, tints):
    palette_path = f"graphics/pokemon/{base.lower()}/normal.pal"
    header, version, count, *colors = read(palette_path).splitlines()
    if (header, version, count) != ("JASC-PAL", "0100", "16") or len(colors) != 16:
        raise SystemExit(f"Invalid palette: {palette_path}")

    for suffix, tint in zip(("normal", "shiny"), tints):
        mapped = [colors[0]]
        for color in colors[1:]:
            rgb = tuple(map(int, color.split()))
            light = (54 * rgb[0] + 183 * rgb[1] + 19 * rgb[2]) / 256
            strength = min(light / 150, 1.0)
            high = max(0, light - 150) / 105
            tone = tuple(channel * strength + (255 - channel) * high for channel in tint)
            tinted = [round(original * 0.32 + hue * 0.68) for original, hue in zip(rgb, tone)]
            mapped.append(" ".join(map(str, tinted)))
        path = f"graphics/pokemon/{base.lower()}/delta_{suffix}.pal"
        write_new(path, "\n".join([header, version, count, *mapped, ""]))
        symbol = f"gReedwake{delta.title().replace('_', '')}{suffix.title()}Palette"
        append("src/data/graphics/pokemon.h",
               f'const u32 {symbol}[] = INCGFX_U32("{path}", ".gbapal.lz");')
        replace("include/graphics.h", "extern const u32 gMonPalette_Bulbasaur[];",
                f"extern const u32 {symbol}[];\nextern const u32 gMonPalette_Bulbasaur[];")
        filename, macro = {
            "normal": ("palette_table.h", "SPECIES_PAL"),
            "shiny": ("shiny_palette_table.h", "SPECIES_SHINY_PAL"),
        }[suffix]
        replace(f"src/data/pokemon_graphics/{filename}",
                f"{macro}({dormant_ids[delta]}, gMon{'Shiny' if suffix == 'shiny' else ''}Palette_DoubleQuestionMark)",
                f"{macro}({delta}, {symbol})")


dormant_ids = {f"DELTA_{identifier(name)}": f"OLD_UNOWN_{letter}"
               for name, (_, letter) in starter_slots.items()}
constants = "include/constants/species.h"
stats_path = "src/data/pokemon/species_info.h"
evo_path = "src/data/pokemon/evolution.h"
ability_constants = read("include/constants/abilities.h")
type_constants = read("include/constants/pokemon.h")
mapping = ["    {SPECIES_BULBASAUR, SPECIES_DELTA_BULBASAUR},"]
evolutions = []

for name, (base, letter) in starter_slots.items():
    entry = entries[name]
    delta = f"DELTA_{identifier(name)}"
    dormant = dormant_ids[delta]
    pattern = rf"(?m)^#define SPECIES_{dormant} \d+$"
    define = re.search(pattern, read(constants))
    if define is None:
        raise SystemExit(f"Missing dormant slot {letter}")
    replace(constants, define[0], define[0] + f"\n#define SPECIES_{delta} SPECIES_{dormant}")

    block = re.search(rf"(?ms)^    \[SPECIES_{base}\] =\n    \{{.*?^    \}},",
                      read(stats_path))
    if block is None:
        raise SystemExit(f"Missing species info for {base}")
    base_type, second_type = (f"TYPE_{identifier(kind)}" for kind in entry["deltaTypes"])
    ability = f"ABILITY_{identifier(entry['deltaAbility'])}"
    if any(f"#define {kind} " not in type_constants for kind in (base_type, second_type)):
        raise SystemExit(f"Unrecognized Delta type for {name}")
    if f"#define {ability} " not in ability_constants:
        raise SystemExit(f"Unrecognized Delta ability for {name}")
    stats = block[0].replace(f"[SPECIES_{base}]", f"[SPECIES_{delta}]", 1)
    stats = re.sub(r"(?m)^(\s*\.types\s*= ).*$",
                   rf"\g<1>{{ {base_type}, {second_type} }},", stats)
    stats = re.sub(r"(?m)^(\s*\.abilities\s*= ).*$",
                   rf"\g<1>{{{ability}, ABILITY_NONE}},", stats)
    replace(stats_path, f"    [SPECIES_{dormant}] = OLD_UNOWN_SPECIES_INFO,", stats)

    for path in (
        "src/data/text/species_names.h",
        "src/data/pokemon/level_up_learnset_pointers.h",
        "src/data/pokemon_graphics/front_pic_table.h",
        "src/data/pokemon_graphics/still_front_pic_table.h",
        "src/data/pokemon_graphics/back_pic_table.h",
        "src/data/pokemon_graphics/front_pic_coordinates.h",
        "src/data/pokemon_graphics/back_pic_coordinates.h",
        "src/data/pokemon_graphics/front_pic_anims.h",
        "src/data/pokemon_graphics/footprint_table.h",
    ):
        clone_row(path, base, dormant, delta)

    make_palette(base, delta, palette_tints[entry["deltaTypes"][1]])
    mapping.append(f"    {{SPECIES_{base}, SPECIES_{delta}}},")
    if entry["evolvesTo"]:
        target = f"SPECIES_DELTA_{identifier(entry['evolvesTo'])}"
        evolutions.append(f"    [SPECIES_{delta}] = {{{{EVO_LEVEL, {entry['evolvesAt']}, {target}}}}},")

evo_opening = "const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] =\n{"
replace(evo_path, evo_opening, evo_opening + "\n" + "\n".join(evolutions))

header = """#ifndef GUARD_REEDWAKE_DELTA_H
#define GUARD_REEDWAKE_DELTA_H

u16 ReedwakeDelta_GetStandardSpecies(u16 species);

#endif
"""
write_new("include/reedwake_delta.h", header)

for path in ("src/pokemon.c", "src/pokemon_icon.c", "src/pokemon_animation.c",
             "src/party_menu.c", "src/daycare.c"):
    replace(path, '#include "global.h"', '#include "global.h"\n#include "reedwake_delta.h"')

path = "src/pokemon.c"
replace(path, "    if (species == SPECIES_DELTA_BULBASAUR)\n        return NATIONAL_DEX_BULBASAUR;",
        "    species = ReedwakeDelta_GetStandardSpecies(species);")
for func in ("SpeciesToHoennPokedexNum", "SpeciesToCryId"):
    start = f"u16 {func}(u16 species)\n{{"
    replace(path, start, start + "\n    species = ReedwakeDelta_GetStandardSpecies(species);")

for func in ("CanMonLearnTMHM", "CanSpeciesLearnTMHM"):
    contents = read(path)
    start = contents.index(f"u32 {func}(")
    pos = contents.index("    // Fewer than 64 moves", start)
    files[path] = contents[:pos] + "    species = ReedwakeDelta_GetStandardSpecies(species);\n\n" + contents[pos:]

replace("src/party_menu.c", "    if (sTutorLearnsets[species] & (1 << tutor))",
        "    if (sTutorLearnsets[ReedwakeDelta_GetStandardSpecies(species)] & (1 << tutor))")
replace("src/daycare.c", "    // Working backwards up to 5 times seems arbitrary",
        "    species = ReedwakeDelta_GetStandardSpecies(species);\n\n"
        "    // Working backwards up to 5 times seems arbitrary")

# Reuse the original icon graphics and back animation for each form.
icons = "src/pokemon_icon.c"
for name, (base, letter) in starter_slots.items():
    delta = f"DELTA_{identifier(name)}"
    dormant = dormant_ids[delta]
    entries_for_base = re.findall(rf"(?m)^    \[SPECIES_{base}\] = .+$", read(icons))
    entries_for_old = re.findall(rf"(?m)^    \[SPECIES_{dormant}\] = .+$", read(icons))
    if len(entries_for_base) != 2 or len(entries_for_old) != 2:
        raise SystemExit(f"Incomplete icon rows for {name}")
    for base_row, old_row in zip(entries_for_base, entries_for_old):
        replace(icons, old_row, base_row.replace(f"SPECIES_{base}", f"SPECIES_{delta}"))
path = "src/pokemon_animation.c"
opening = "static const u8 sSpeciesToBackAnimSet[] =\n{"
if opening not in read(path):
    raise SystemExit("Missing back animation table")
for name, (base, _) in starter_slots.items():
    row = re.search(rf"(?m)^    \[SPECIES_{base}\]\s+= BACK_ANIM_[A-Z_]+,",
                    read(path))
    if row is None:
        raise SystemExit(f"Missing back animation for {name}")
    replace(path, row[0], row[0] + "\n" + row[0].replace(f"SPECIES_{base}", f"SPECIES_DELTA_{identifier(name)}"))

script_path = "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"
machine_call = "\tmsgbox LittlerootTown_ProfessorBirchsLab_Text_SeriousLookingMachine, MSGBOX_SIGN"
replace(script_path, "LittlerootTown_ProfessorBirchsLab_EventScript_Machine::\n" + machine_call,
        "LittlerootTown_ProfessorBirchsLab_EventScript_Machine::\n"
        "\tgoto_if_set FLAG_SYS_POKEDEX_GET, ReedwakeDelta_EventScript_Lab\n" + machine_call)

templates = Path(__file__).with_name("reedwake_delta")
append(script_path, (templates / "lab.inc").read_text(encoding="utf-8"))
write_new("src/reedwake_delta.c", (templates / "delta.c").read_text(encoding="utf-8")
          .replace("    /* Delta mapping */", "\n".join(mapping)))
append("data/specials.inc", "\tdef_special ReedwakeDelta_CheckSelected\n\tdef_special ReedwakeDelta_ConvertSelected")

wild = "src/wild_encounter.c"
replace(wild, '#include "bulbasaur_field_notes.h"\n', "")
replace(wild,
        "    if (area == WILD_AREA_LAND && BulbasaurNotes_OfferDeltaEncounter())\n"
        "        CreateWildMon(SPECIES_DELTA_BULBASAUR, level);\n"
        "    else\n"
        "        CreateWildMon(wildMonInfo->wildPokemon[wildMonIndex].species, level);",
        "    CreateWildMon(wildMonInfo->wildPokemon[wildMonIndex].species, level);")
notes = "src/bulbasaur_field_notes.c"
contents = read(notes)
cut = contents.index("    if (gBattleOutcome == B_OUTCOME_CAUGHT")
files[notes] = contents[:cut] + "}\n"
replace("include/bulbasaur_field_notes.h", "bool8 BulbasaurNotes_OfferDeltaEncounter(void);\n", "")
replace("include/bulbasaur_field_notes.h", "BULBASAUR_NOTES_DELTA_CAUGHT", "BULBASAUR_NOTES_DELTA_CONVERTED")
replace("src/pokedex.c", 'static const u8 sDeltaUnlocked[] = _("Unlocked: Bulbasaur");',
        'static const u8 sDeltaUnlocked[] = _("Ready: Brackenhaven Lab");')

for path, contents in files.items():
    original = source / path
    if not original.exists() or original.read_text(encoding="utf-8") != contents:
        original.write_text(contents, encoding="utf-8")
