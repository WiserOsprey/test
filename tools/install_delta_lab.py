#!/usr/bin/env python3
"""Install Reedwake's permanent Delta forms and the field lab."""
import json
import re
import sys
from pathlib import Path

from PIL import Image

from emerald_sprites import install_pair

roster_path, source, assets = map(Path, sys.argv[1:4])
roster = json.loads(roster_path.read_text(encoding="utf-8"))
entries = {entry["name"]: entry for entry in roster["species"]}

# These dormant Emerald slots precede the Hoenn species range.
delta_slots = {
    "Fernut": ("TREECKO", "C"),
    "Bramblet": ("GROVYLE", "D"),
    "Canoplate": ("SCEPTILE", "E"),
    "Cindrix": ("TORCHIC", "F"),
    "Flareden": ("COMBUSKEN", "G"),
    "Vulprism": ("BLAZIKEN", "H"),
    "Rillfin": ("MUDKIP", "I"),
    "Bendruff": ("MARSHTOMP", "J"),
    "Estuarch": ("SWAMPERT", "K"),
    "Siltmole": ("GEODUDE", "L"),
    "Gategrub": ("GRAVELER", "M"),
    "Lockmole": ("GOLEM", "N"),
    "Sporelet": ("SHROOMISH", "O"),
    "Budwing": ("BRELOOM", "P"),
    "Graftwing": ("HERACROSS", "Q"),
    "Gullit": ("TAILLOW", "R"),
    "Vaneagle": ("SWELLOW", "S"),
    "Galegull": ("TROPIUS", "T"),
}
delta_moves = {
    "Fernut": [(9, "THUNDER_SHOCK"), (24, "SPARK")],
    "Bramblet": [(9, "THUNDER_SHOCK"), (24, "SPARK"), (39, "THUNDERBOLT")],
    "Canoplate": [(12, "ROCK_THROW"), (24, "SPARK"), (42, "ROCK_SLIDE"), (48, "THUNDERBOLT")],
    "Cindrix": [(9, "ASTONISH"), (24, "NIGHT_SHADE")],
    "Flareden": [(9, "ASTONISH"), (24, "NIGHT_SHADE"), (39, "SHADOW_BALL")],
    "Vulprism": [(12, "CONFUSION"), (22, "BITE"), (42, "CRUNCH"), (48, "PSYCHIC")],
    "Rillfin": [(12, "ICY_WIND"), (26, "AURORA_BEAM")],
    "Bendruff": [(12, "ICY_WIND"), (26, "AURORA_BEAM"), (41, "ICE_BEAM")],
    "Estuarch": [(12, "ICY_WIND"), (19, "DOUBLE_KICK"), (40, "BRICK_BREAK"), (47, "ICE_BEAM")],
    "Siltmole": [(7, "WATER_GUN"), (18, "BUBBLE_BEAM")],
    "Gategrub": [(7, "WATER_GUN"), (19, "WATER_PULSE"), (36, "MUDDY_WATER")],
    "Lockmole": [(7, "WATER_GUN"), (19, "WATER_PULSE"), (36, "MUDDY_WATER")],
    "Sporelet": [(7, "POISON_POWDER"), (19, "ACID")],
    "Budwing": [(5, "POISON_POWDER"), (19, "ACID"), (32, "SLUDGE")],
    "Graftwing": [(10, "ACID"), (23, "SLUDGE"), (37, "SLUDGE_BOMB")],
    "Gullit": [(7, "THUNDER_SHOCK"), (16, "SPARK"), (28, "SHOCK_WAVE")],
    "Vaneagle": [(8, "THUNDER_SHOCK"), (18, "SPARK"), (25, "SHOCK_WAVE"), (39, "THUNDERBOLT")],
    "Galegull": [(10, "THUNDER_SHOCK"), (20, "SPARK"), (28, "SHOCK_WAVE"), (37, "THUNDERBOLT")],
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


def install_delta_art(name, base, delta):
    """Keep the engine's frame count and give the Delta form its own sprite data."""
    original = source / "graphics/pokemon" / base.lower()
    with Image.open(original / "anim_front.png") as sheet:
        animation_size = sheet.size

    art = assets / name.lower()
    output = source / "graphics/pokemon/reedwake_delta" / name.lower()
    install_pair(art / "front.png", art / "back.png", output, animation_size)

    for filename, macro, graphic, file, extension in (
        ("front_pic_table.h", "SPECIES_SPRITE", "FrontPic", "anim_front.png", ".4bpp.lz"),
        ("still_front_pic_table.h", "SPECIES_SPRITE", "StillFrontPic", "front.png", ".4bpp.lz"),
        ("back_pic_table.h", "SPECIES_SPRITE", "BackPic", "back.png", ".4bpp.lz"),
        ("palette_table.h", "SPECIES_PAL", "Palette", "normal.pal", ".gbapal.lz"),
        ("shiny_palette_table.h", "SPECIES_SHINY_PAL", "ShinyPalette", "shiny.pal", ".gbapal.lz"),
    ):
        symbol = f"gReedwakeDelta{identifier(name).title()}{graphic}"
        asset_file = (output / file).relative_to(source).as_posix()
        append("src/data/graphics/pokemon.h",
               f'const u32 {symbol}[] = INCGFX_U32("{asset_file}", "{extension}");')
        replace("include/graphics.h", "extern const u32 gMonPalette_Bulbasaur[];",
                f"extern const u32 {symbol}[];\nextern const u32 gMonPalette_Bulbasaur[];")

        table = f"src/data/pokemon_graphics/{filename}"
        old = dormant_ids[delta] if graphic.endswith("Palette") else delta
        pattern = rf"\b{macro}\({old},\s*\w+\)"
        row = re.search(pattern, read(table))
        if row is None:
            raise SystemExit(f"Missing {old} in {table}")
        replace(table, row[0], f"{macro}({delta}, {symbol})")


def install_delta_learnset(name, delta):
    path = "src/data/pokemon/level_up_learnset_pointers.h"
    line = re.search(rf"(?m)^    \[SPECIES_{delta}\] = (\w+),$", read(path))
    if line is None:
        raise SystemExit(f"Missing learnset pointer for {name}")
    base_learnset = line[1]
    data_path = "src/data/pokemon/level_up_learnsets.h"
    original = re.search(rf"(?ms)^static const u16 {base_learnset}\[\] = \{{(.*?)^\}};",
                         read(data_path))
    if original is None:
        raise SystemExit(f"Missing level-up moves for {name}")
    moves = [(int(level), move) for level, move in
             re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*MOVE_(\w+)\)", original[1])]
    existing = {move for _, move in moves}
    moves.extend((level, move) for level, move in delta_moves[name] if move not in existing)
    moves.sort(key=lambda pair: pair[0])
    name = f"sReedwakeDelta{name}LevelUpLearnset"
    rows = "\n".join(f"    LEVEL_UP_MOVE({level:2d}, MOVE_{move})," for level, move in moves)
    append(data_path, f"static const u16 {name}[] = {{\n{rows}\n    LEVEL_UP_END\n}};")
    replace(path, line[0], f"    [SPECIES_{delta}] = {name},")

dormant_ids = {f"DELTA_{identifier(name)}": f"OLD_UNOWN_{letter}"
               for name, (_, letter) in delta_slots.items()}
constants = "include/constants/species.h"
stats_path = "src/data/pokemon/species_info.h"
evo_path = "src/data/pokemon/evolution.h"
ability_constants = read("include/constants/abilities.h")
type_constants = read("include/constants/pokemon.h")
mapping = ["    {SPECIES_BULBASAUR, SPECIES_DELTA_BULBASAUR},"]
evolutions = []

for name, (base, letter) in delta_slots.items():
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

    install_delta_art(name, base, delta)
    install_delta_learnset(name, delta)
    mapping.append(f"    {{SPECIES_{base}, SPECIES_{delta}}},")
    if entry["evolvesTo"]:
        target = f"SPECIES_DELTA_{identifier(entry['evolvesTo'])}"
        evolutions.append(f"    [SPECIES_{delta}] = {{{{EVO_LEVEL, {entry['evolvesAt']}, {target}}}}},")

evo_opening = "const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] =\n{"
replace(evo_path, evo_opening, evo_opening + "\n" + "\n".join(evolutions))

header = """#ifndef GUARD_REEDWAKE_DELTA_H
#define GUARD_REEDWAKE_DELTA_H

u16 ReedwakeDelta_GetStandardSpecies(u16 species);
void ReedwakeDelta_StartBattle(void);
void ReedwakeDelta_RecordMove(u8 battler, u16 move);
void ReedwakeDelta_FinishBattle(void);

#endif
"""
write_new("include/reedwake_delta.h", header)

replace("include/constants/vars.h", "VAR_UNUSED_0x40F8                                0x40F8 // Unused Var",
        "VAR_REEDWAKE_FIELD_TRIALS                      0x40F8")
for path in ("src/battle_main.c", "src/battle_script_commands.c"):
    replace(path, '#include "bulbasaur_field_notes.h"',
            '#include "bulbasaur_field_notes.h"\n#include "reedwake_delta.h"')
replace("src/battle_main.c", "    BulbasaurNotes_StartBattle();",
        "    BulbasaurNotes_StartBattle();\n    ReedwakeDelta_StartBattle();")
replace("src/battle_main.c", "    BulbasaurNotes_FinishBattle();",
        "    BulbasaurNotes_FinishBattle();\n    ReedwakeDelta_FinishBattle();")
replace("src/battle_script_commands.c", "        BulbasaurNotes_RecordMove(gBattlerAttacker, gCurrentMove);",
        "        BulbasaurNotes_RecordMove(gBattlerAttacker, gCurrentMove);\n"
        "        ReedwakeDelta_RecordMove(gBattlerAttacker, gCurrentMove);")

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
for name, (base, letter) in delta_slots.items():
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
for name, (base, _) in delta_slots.items():
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


def replace_dialogue(path, label, lines):
    pattern = rf"(?m)^{label}:\n(?:\t\.string .+\n)+"
    match = re.search(pattern, read(path))
    if match is None:
        raise SystemExit(f"Missing dialogue {label} in {path}")
    text = label + ":\n" + "".join(f'\t.string "{line}"\n' for line in lines)
    replace(path, match[0], text)


for route, name in ((101, "BRACKEN TRAIL"), (102, "REEDBANK PATH"), (103, "TIDE REACH")):
    route_marker = f'"id": "MAPSEC_ROUTE_{route}",\n      "name": '
    replace("src/data/region_map/region_map_sections.json",
            f'{route_marker}"ROUTE {route}"', f'{route_marker}"{name}"')

path = "data/maps/Route101/scripts.inc"
replace_dialogue(path, "Route101_Text_PleaseHelp",
                 [r"The relay spooked that POKéMON!\p",
                  r"Take a partner from my survey bag.\n",
                  r"One of them can calm it down!$"])
replace_dialogue(path, "Route101_Text_YouSavedMe",
                 [r"PROF. BIRCH: Thank you, {PLAYER}.\p",
                  r"I was measuring the relay when it\n",
                  r"sent a pulse through the reeds.\p",
                  r"That SILTSTILT felt it before I did.\n",
                  r"We should talk at the lab.$"])
replace_dialogue(path, "Route101_Text_RouteSign",
                 [r"BRACKEN TRAIL / ROUTE 101\n", r"{UP_ARROW} OLDALE TOWN$"])
replace_dialogue("data/maps/Route102/scripts.inc", "Route102_Text_RouteSignOldale",
                 [r"REEDBANK PATH / ROUTE 102\n", r"{RIGHT_ARROW} OLDALE TOWN$"])
replace_dialogue("data/maps/Route102/scripts.inc", "Route102_Text_RouteSignPetalburg",
                 [r"REEDBANK PATH / ROUTE 102\n", r"{LEFT_ARROW} PETALBURG CITY$"])

path = "data/maps/Route103/scripts.inc"
for rival in ("May", "Brendan"):
    prefix = f"Route103_Text_{rival}"
    replace_dialogue(path, prefix + "Route103Pokemon",
                     [r"IONA: The tide's coming in early.\n",
                      r"Look at these marks on the stakes.$"])
    replace_dialogue(path, prefix + "LetsBattle",
                     [r"IONA: Hey, {PLAYER}. You got a partner!\p",
                      r"Mine picked up a pulse from the water.\n",
                      r"Let's battle and see how they react!$"])
    replace_dialogue(path, prefix + "Defeated",
                     [r"You read your partner faster than\n", r"I read mine. Good battle!$"])
    replace_dialogue(path, prefix + "TimeToHeadBack",
                     [r"IONA: Did you notice? The pulse stopped\n",
                      r"the second the battle ended.\p",
                      r"I'm writing it down. Let's bring our\n",
                      r"readings to the BRACKENHAVEN lab.$"])
replace_dialogue(path, "Route103_Text_RouteSign",
                 [r"TIDE REACH / ROUTE 103\n", r"{DOWN_ARROW} OLDALE TOWN$"])

path = "src/data/trainers.h"
for rival in ("MAY", "BRENDAN"):
    for starter in ("MUDKIP", "TREECKO", "TORCHIC"):
        pattern = rf"(?ms)^\s*\[TRAINER_{rival}_ROUTE_103_{starter}\].*?^    \}},"
        trainer = re.search(pattern, read(path))
        if trainer is None:
            raise SystemExit(f"Missing Tide Reach rival for {rival} and {starter}")
        replace(path, trainer[0], trainer[0].replace(f'.trainerName = _("{rival}")',
                                                   '.trainerName = _("IONA")'))

path = "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"
prefix = "LittlerootTown_ProfessorBirchsLab_Text_"
replace_dialogue(path, prefix + "LikeYouToHavePokemon",
                 [r"PROF. BIRCH: These relays used to keep\n",
                  r"time with the tide.\p",
                  r"Now the readings drift further apart\n",
                  r"every day. I need another surveyor.\p",
                  r"Your partner trusted you out there.\n",
                  r"I'd like the two of you to keep at it.\p",
                  r"{PLAYER} received the {STR_VAR_1}!$"])
replace_dialogue(path, prefix + "MightBeGoodIdeaToGoSeeRival",
                 [r"PROF. BIRCH: IONA took the north trail\n",
                  r"to check the tide stakes.\p",
                  r"Will you meet her at TIDE REACH?$"])
replace_dialogue(path, prefix + "GetRivalToTeachYou",
                 [r"PROF. BIRCH: Head north past OLDALE.\p",
                  r"IONA will show you the highest tide\n",
                  r"mark she found. I'll wait here.$"])
replace_dialogue(path, prefix + "ExplainPokedex",
                 [r"PROF. BIRCH: This POKéDEX can record\n",
                  r"the signals your partners give off.\p",
                  r"Battle on the survey trails to collect\n",
                  r"readings under field conditions.\p",
                  r"Bring them to my RESONANCE LAB table.\n",
                  r"Start with the machine by the wall.$"])

for path, contents in files.items():
    original = source / path
    if not original.exists() or original.read_text(encoding="utf-8") != contents:
        original.write_text(contents, encoding="utf-8")
