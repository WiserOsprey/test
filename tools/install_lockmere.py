#!/usr/bin/env python3
"""Lay out the Lockmere gym, its puzzle and the first district's encounters."""
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from emerald_sprites import fit_sprite, index_sprite

source, assets = map(Path, sys.argv[1:3])


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise SystemExit(f"Expected one source match for {before[:80]!r}")
    return text.replace(before, after, 1)


def replace_dialogue(text, label, lines):
    block = re.search(rf"(?m)^{label}:\n(?:\t\.string .+\n)+", text)
    if block is None:
        raise SystemExit(f"Missing dialogue {label}")
    replacement = label + ":\n" + "".join(f'\t.string "{line}"\n' for line in lines)
    return replace_once(text, block[0], replacement)


def make_gym_tiles():
    tileset = source / "data/tilesets/secondary/rustboro_gym"
    colors = [
        (0, 0, 0), (16, 24, 37), (24, 40, 58), (33, 56, 74),
        (41, 73, 83), (49, 98, 105), (74, 132, 131), (115, 179, 157),
        (156, 214, 183), (57, 43, 45), (90, 61, 47), (132, 89, 61),
        (180, 131, 75), (230, 180, 101), (230, 230, 193), (189, 80, 65),
    ]
    art = {}
    for name, color in (
        ("floor", 3), ("water", 2), ("gate", 2), ("crossing", 10),
        ("intake", 3), ("fill", 3), ("relief", 3), ("gauge", 3), ("station", 3),
    ):
        art[name] = Image.new("P", (16, 16), color)

    draw = ImageDraw.Draw(art["floor"])
    draw.rectangle((0, 0, 15, 15), outline=2)
    draw.line((1, 1, 14, 1), fill=4)
    draw.line((1, 7, 4, 7), fill=2)
    draw.point([(6, 5), (12, 11), (1, 13)], fill=4)
    draw.line((4, 13, 8, 13), fill=2)

    draw = ImageDraw.Draw(art["water"])
    for points in (
        [(1, 3), (4, 3), (5, 2), (9, 2)],
        [(7, 8), (12, 8), (13, 7), (15, 7)],
        [(0, 13), (4, 13), (5, 12), (9, 12)],
    ):
        draw.line(points, fill=4)
    draw.point([(0, 4), (7, 2), (10, 8), (3, 13)], fill=5)

    draw = ImageDraw.Draw(art["gate"])
    draw.rectangle((0, 2, 15, 13), fill=1, outline=5)
    draw.line((1, 3, 14, 3), fill=7)
    for x in (2, 6, 10, 14):
        draw.line((x, 5, x, 11), fill=4)
    draw.line((1, 10, 14, 10), fill=3)
    draw.point([(2, 3), (13, 3), (2, 12), (13, 12)], fill=13)

    draw = ImageDraw.Draw(art["crossing"])
    for y in (0, 4, 8, 12):
        draw.line((2, y, 13, y), fill=12)
        draw.line((2, y + 3, 13, y + 3), fill=9)
    draw.line((1, 0, 1, 15), fill=5, width=2)
    draw.line((14, 0, 14, 15), fill=5, width=2)
    draw.point([(1, 1), (1, 14), (14, 1), (14, 14)], fill=8)

    for name, main_color, edge_color in (
        ("intake", 12, 13), ("fill", 15, 13), ("relief", 6, 8),
    ):
        draw = ImageDraw.Draw(art[name])
        draw.rectangle((1, 2, 14, 14), fill=1)
        draw.rectangle((2, 2, 13, 13), fill=4, outline=6)
        draw.ellipse((3, 2, 12, 11), fill=1, outline=edge_color)
        draw.line((7, 3, 7, 10), fill=main_color, width=2)
        draw.line((4, 6, 11, 6), fill=main_color, width=2)
        draw.point((7, 6), fill=14)

    draw = ImageDraw.Draw(art["gauge"])
    draw.rectangle((2, 2, 13, 13), fill=1, outline=5)
    draw.ellipse((3, 3, 12, 12), fill=3, outline=13)
    draw.arc((5, 5, 10, 10), 180, 360, fill=8)
    draw.line((7, 8, 10, 6), fill=15)
    draw.point((7, 8), fill=14)

    draw = ImageDraw.Draw(art["station"])
    draw.rectangle((2, 2, 13, 14), fill=1, outline=5)
    draw.rectangle((4, 3, 11, 8), fill=5, outline=7)
    draw.line((5, 7, 6, 5, 8, 6, 10, 4), fill=8)
    draw.line((4, 10, 11, 10), fill=6)
    draw.point([(5, 12), (8, 12), (10, 12)], fill=13)

    tiles_path = tileset / "tiles.png"
    with Image.open(tiles_path) as image:
        original = image.copy()
    if original.mode != "P" or original.width != 128 or original.height % 8:
        raise SystemExit("Unexpected Lockmere source tile sheet")
    old_tiles = (original.width * original.height) // 64
    width_in_tiles = original.width // 8
    palette_number = 12
    palette = tileset / f"palettes/{palette_number:02}.pal"
    palette.write_text("JASC-PAL\n0100\n16\n" + "\n".join(
        " ".join(map(str, rgb)) for rgb in colors) + "\n", encoding="ascii")
    sheet_height = original.height + ((len(art) * 4 + width_in_tiles - 1) // width_in_tiles) * 8
    sheet = Image.new("P", (original.width, sheet_height))
    sheet.putpalette(original.getpalette())
    sheet.paste(original, (0, 0))

    metatiles_path = tileset / "metatiles.bin"
    attrs_path = tileset / "metatile_attributes.bin"
    metatiles = bytearray(metatiles_path.read_bytes())
    attrs = bytearray(attrs_path.read_bytes())
    if len(metatiles) != 16 * (len(attrs) // 2):
        raise SystemExit("Lockmere tile data and behavior data disagree")

    ids = {}
    for name, image in art.items():
        ids[name] = 512 + len(metatiles) // 16
        entries = []
        for off_y in (0, 8):
            for off_x in (0, 8):
                subtile = image.crop((off_x, off_y, off_x + 8, off_y + 8))
                x = (old_tiles % width_in_tiles) * 8
                y = (old_tiles // width_in_tiles) * 8
                sheet.paste(subtile, (x, y))
                entries.append((512 + old_tiles) | (palette_number << 12))
                old_tiles += 1
        metatiles.extend(struct.pack("<8H", *entries, 0, 0, 0, 0))
        attrs.extend(struct.pack("<H", 0))  # Normal floor behavior; map blocks set collision.
    sheet.save(tiles_path, bits=4)
    metatiles_path.write_bytes(metatiles)
    attrs_path.write_bytes(attrs)
    return ids


def build_gym_map(ids):
    map_path = source / "data/layouts/RustboroCity_Gym/map.bin"
    data = map_path.read_bytes()
    if len(data) != 11 * 20 * 2:
        raise SystemExit("Unexpected Lockmere Gym map dimensions")
    blocks = list(struct.unpack("<220H", data))

    def place(x, y, tile, blocked=False):
        blocks[y * 11 + x] = tile | 0x3000 | (0x400 if blocked else 0)

    for y in range(2, 20):
        for x in range(11):
            if x in (0, 10):
                place(x, y, 0x223, True)
            elif y in (7, 12):
                place(x, y, ids["gate" if x in (5, 6) else "water"], True)
            else:
                place(x, y, ids["floor"])
    for x in (5, 6):
        for y in (6, 8, 11, 13, 14):
            place(x, y, ids["crossing"])
    for name, x, y in (("intake", 2, 15), ("fill", 2, 9), ("gauge", 5, 9), ("relief", 8, 9), ("station", 8, 4)):
        place(x, y, ids[name], True)
    place(2, 18, 0x226, True)
    place(8, 18, 0x226, True)
    # Preserve both exits and the chamber walls from the room layout.
    for x, tile in ((5, 0x006), (6, 0x007)):
        place(x, 19, tile)
    map_path.write_bytes(struct.pack("<220H", *blocks))

    events_path = source / "data/maps/RustboroCity_Gym/map.json"
    events = json.loads(events_path.read_text(encoding="utf-8"))
    coords = { "Josh": (8, 15), "Tommy": (3, 11), "Marc": (2, 4) }
    for event in events["object_events"]:
        label = event["script"].rsplit("_", 1)[-1]
        if label in coords:
            event["x"], event["y"] = coords[label]
            event["trainer_sight_or_berry_tree_id"] = "1"
            event["movement_type"] = "MOVEMENT_TYPE_FACE_DOWN"
            event["movement_range_x"] = event["movement_range_y"] = 0
    for x, y, script in (
        (2, 15, "Lockmere_OpenIntake"), (2, 9, "Lockmere_FillValve"),
        (5, 9, "Lockmere_ReadGauge"), (8, 9, "Lockmere_ReliefValve"),
        (8, 4, "Lockmere_FieldStation"),
    ):
        events["bg_events"].append({
            "type": "sign", "x": x, "y": y, "elevation": 0,
            "player_facing_dir": "BG_EVENT_PLAYER_FACING_NORTH", "script": script,
        })
    events_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")


ids = make_gym_tiles()
build_gym_map(ids)

vars_path = source / "include/constants/vars.h"
vars_path.write_text(replace_once(vars_path.read_text(encoding="utf-8"),
    "VAR_UNUSED_0x40F9                                0x40F9 // Unused Var",
    "VAR_LOCKMERE_WATER_LEVEL                        0x40F9"), encoding="utf-8")

path = source / "data/maps/RustboroCity_Gym/scripts.inc"
gym = path.read_text(encoding="utf-8")
gym = replace_once(gym, "RustboroCity_Gym_MapScripts::\n\t.byte 0",
    "RustboroCity_Gym_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Lockmere_LoadState\n\t.byte 0")
gym = replace_once(gym, "RustboroCity_Gym_EventScript_Roxanne::\n",
    "RustboroCity_Gym_EventScript_Roxanne::\n"
    "\tgoto_if_lt VAR_LOCKMERE_WATER_LEVEL, 2, Lockmere_SendToEntrance\n")
gym += "\nLockmere_LoadState:\n\tgoto_if_set FLAG_BADGE01_GET, Lockmere_LoadAfterBadge\n"
gym += "\tcall Lockmere_ApplyWaterLevel\n\tend\n"
gym += "\nLockmere_LoadAfterBadge:\n\tsetvar VAR_LOCKMERE_WATER_LEVEL, 2\n\tcall Lockmere_ApplyWaterLevel\n\tend\n"
gym += "\nLockmere_SendToEntrance:\n\tlockall\n\tgoto Lockmere_ReleaseStuck\n"
script = Path(__file__).with_name("lockmere_gates.inc").read_text(encoding="utf-8")
gym += "\n" + script.replace("@CROSSING@", f"0x{ids['crossing']:03X}")

gym_dialogue = {
    "GymGuideAdvice": [
        r"The old lock flooded overnight.\p",
        r"Open the intake in the west bay to\n",
        r"cross the first channel. Read the\n",
        r"gauge before turning a second wheel.\p",
        r"TAMSIN uses GROUND types. PEATHARE's\n",
        r"GRASS moves work on the smaller ones.\n",
        r"Pack a WATER move for her LOCKMOLE.$",
    ],
    "GymGuidePostVictory": [
        r"You kept both chambers draining.\n", r"The lock crew can work again.$",
    ],
    "RoxanneIntro": [
        r"TAMSIN: That was the right wheel.\p",
        r"I run this lock with my partners.\n",
        r"They dig the bypasses we can't reach.\p",
        r"Show me how you work with yours!$",
    ],
    "RoxanneDefeat": [
        r"TAMSIN: You read my team as carefully\n",
        r"as you read the gauge.\p",
        r"The whole district could use a partner\n",
        r"like that. The STONE BADGE is yours.$",
    ],
    "ReceivedStoneBadge": [r"{PLAYER} received the STONE BADGE\n", r"from TAMSIN.$"],
    "RoxannePostBattle": [
        r"The upper relay still won't answer.\n", r"I'll keep these gates open for you.$",
    ],
    "GymStatue": [r"LOCKMERE GYM\p", r"WATERWORKS CERTIFICATION\n", r"LEADER: TAMSIN$"],
    "GymStatueCertified": [
        r"LOCKMERE GYM\p", r"APPRENTICES CERTIFIED BY TAMSIN:\n", r"{PLAYER}$",
    ],
    "JoshIntro": [r"I work the lower lock. Can your team\n", r"hold its ground against mine?$"],
    "JoshDefeat": [r"I lost my footing there.$"],
    "JoshPostBattle": [r"The west bay holds the intake vane.$"],
    "TommyIntro": [r"This is the gauge deck. Let's see if\n", r"you can read my team's moves.$"],
    "TommyDefeat": [r"You saw that one coming!$"],
    "TommyPostBattle": [r"Check that gauge before turning a wheel.$"],
    "MarcIntro": [r"The arena's just ahead. Show me\n", r"what you learned at the gates.$"],
    "MarcDefeat": [r"That earns you passage.$"],
    "MarcPostBattle": [r"TAMSIN's LOCKMOLE is tough. Its steel\n", r"plates turn aside a lot of attacks.$"],
}
for label, lines in gym_dialogue.items():
    gym = replace_dialogue(gym, "RustboroCity_Gym_Text_" + label, lines)
gym = gym.replace("ROXANNE", "TAMSIN").replace("RUSTBORO CITY", "LOCKMERE")
# Internal trainer and flag IDs keep their original numeric values.
gym = gym.replace("TRAINER_TAMSIN_", "TRAINER_ROXANNE_").replace("FLAG_ENABLE_TAMSIN_", "FLAG_ENABLE_ROXANNE_")
path.write_text(gym, encoding="utf-8")


# Keep the existing battle and badge IDs so gym wins and rematches still
# participate in the engine's progression flags.
path = source / "src/data/trainers.h"
trainers = path.read_text(encoding="utf-8")
if not re.search(r'\[TRAINER_ROXANNE_1\][\s\S]{0,350}\.trainerName = _\("ROXANNE"\)', trainers):
    raise SystemExit("Missing the first gym leader")
path.write_text(trainers.replace('.trainerName = _("ROXANNE")', '.trainerName = _("TAMSIN")'), encoding="utf-8")

path = source / "src/data/trainer_parties.h"
parties = path.read_text(encoding="utf-8")
first_gym = re.search(r"(?ms)^static const struct TrainerMonItemCustomMoves sParty_Roxanne1\[\] = \{.*?^\};", parties)
if first_gym is None:
    raise SystemExit("Missing the first gym party")
party = """static const struct TrainerMonItemCustomMoves sParty_Roxanne1[] = {
    {
        .iv = 95,
        .lvl = 11,
        .species = SPECIES_GEODUDE,
        .heldItem = ITEM_NONE,
        .moves = {MOVE_SCRATCH, MOVE_MUD_SLAP, MOVE_SAND_ATTACK, MOVE_NONE}
    },
    {
        .iv = 110,
        .lvl = 12,
        .species = SPECIES_GRAVELER,
        .heldItem = ITEM_NONE,
        .moves = {MOVE_ROCK_THROW, MOVE_MUD_SLAP, MOVE_DEFENSE_CURL, MOVE_NONE}
    },
    {
        .iv = 130,
        .lvl = 14,
        .species = SPECIES_GOLEM,
        .heldItem = ITEM_ORAN_BERRY,
        .moves = {MOVE_MUD_SHOT, MOVE_METAL_CLAW, MOVE_SCRATCH, MOVE_HARDEN}
    }
};"""
parties = replace_once(parties, first_gym[0], party)
josh = re.search(r"(?ms)^static const struct TrainerMonNoItemCustomMoves sParty_Josh\[\] = \{.*?^\};", parties)
if josh is None:
    raise SystemExit("Missing the intake trainer")
parties = replace_once(parties, josh[0],
    josh[0].replace("MOVE_TACKLE, MOVE_NONE", "MOVE_SCRATCH, MOVE_MUD_SLAP", 1))
path.write_text(parties, encoding="utf-8")

tamsin = fit_sprite(assets / "tamsin.png")
visible = [pixel[:3] for pixel in tamsin.getdata() if pixel[3]]
sample = Image.new("RGB", (len(visible), 1))
sample.putdata(visible)
quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
palette = quantized.getpalette()[:45]
colors = [(0, 0, 0), *(tuple(palette[i:i + 3]) for i in range(0, 45, 3))]
index_sprite(tamsin, colors).save(source / "graphics/trainers/front_pics/leader_roxanne.png",
                                  bits=4, transparency=0)

path = source / "src/data/region_map/region_map_sections.json"
region = json.loads(path.read_text(encoding="utf-8"))
names = {
    "MAPSEC_RUSTBORO_CITY": "LOCKMERE",
    "MAPSEC_ROUTE_104": "ALDERBANK",
    "MAPSEC_ROUTE_116": "LOCKMERE CUT",
    "MAPSEC_RUSTURF_TUNNEL": "GATEWORKS TUNNEL",
}
for area in region["map_sections"]:
    if area["id"] in names:
        area["name"] = names[area["id"]]
path.write_text(json.dumps(region, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

path = source / "data/maps/RustboroCity/scripts.inc"
city = path.read_text(encoding="utf-8")
city = replace_dialogue(city, "RustboroCity_Text_GymSign",
    [r"LOCKMERE WATERWORKS\p", r"GYM LEADER: TAMSIN\n", r"GROUND TYPE CERTIFICATION$"])
city = replace_dialogue(city, "RustboroCity_Text_CitySign",
    [r"LOCKMERE\p", r"The first lock between the coast\n", r"and the upper fields.$"])
path.write_text(city, encoding="utf-8")

path = source / "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc"
lab = path.read_text(encoding="utf-8")
lab = replace_once(lab, '\t.string "Start with the machine by the wall.$"',
    '\t.string "Start with the machine by the wall.\\p"\n'
    '\t.string "TAMSIN needs a surveyor at LOCKMERE.\\n"\n'
    '\t.string "Head west through REEDBANK, then\\l"\n'
    '\t.string "north through the woods.$"')
path.write_text(lab, encoding="utf-8")

# Standard forms can be caught before the trial. Late encounter slots
# make mature stages much rarer than the young ones in the same habitat.
encounters = {
    "MAP_ROUTE102": [
        ("POOCHYENA", 3), ("WURMPLE", 3), ("POOCHYENA", 4), ("WURMPLE", 4),
        ("ZIGZAGOON", 3), ("ZIGZAGOON", 4), ("POOCHYENA", 4), ("ZIGZAGOON", 4),
        ("WURMPLE", 4), ("ZIGZAGOON", 4), ("POOCHYENA", 4), ("WURMPLE", 4),
    ],
    "MAP_ROUTE103": [
        ("ZIGZAGOON", 3), ("POOCHYENA", 3), ("ZIGZAGOON", 4), ("POOCHYENA", 4),
        ("WURMPLE", 3), ("ZIGZAGOON", 3), ("ZIGZAGOON", 4), ("POOCHYENA", 4),
        ("WURMPLE", 4), ("POOCHYENA", 4), ("ZIGZAGOON", 4), ("WURMPLE", 4),
    ],
    "MAP_ROUTE104": [
        ("ZIGZAGOON", 5), ("POOCHYENA", 5), ("POOCHYENA", 6), ("WURMPLE", 5),
        ("ZIGZAGOON", 6), ("WURMPLE", 6), ("ZIGZAGOON", 6), ("MUDKIP", 6),
        ("POOCHYENA", 6), ("WURMPLE", 6), ("SILCOON", 7), ("MUDKIP", 7),
    ],
    "MAP_PETALBURG_WOODS": [
        ("WURMPLE", 5), ("POOCHYENA", 5), ("WURMPLE", 6), ("POOCHYENA", 6),
        ("ZIGZAGOON", 5), ("WURMPLE", 6), ("SILCOON", 7), ("POOCHYENA", 7),
        ("ZIGZAGOON", 6), ("WURMPLE", 7), ("SILCOON", 8), ("BEAUTIFLY", 10),
    ],
    "MAP_ROUTE116": [
        ("GEODUDE", 7), ("POOCHYENA", 7), ("GEODUDE", 8), ("ZIGZAGOON", 8),
        ("POOCHYENA", 8), ("GEODUDE", 8), ("WURMPLE", 7), ("GEODUDE", 9),
        ("ZIGZAGOON", 8), ("POOCHYENA", 9), ("GEODUDE", 9), ("GRAVELER", 12),
    ],
    "MAP_RUSTURF_TUNNEL": [
        ("GEODUDE", 6), ("GEODUDE", 7), ("GEODUDE", 7), ("GEODUDE", 8),
        ("GEODUDE", 8), ("GEODUDE", 8), ("GEODUDE", 9), ("GEODUDE", 9),
        ("GEODUDE", 9), ("GEODUDE", 10), ("GEODUDE", 10), ("GRAVELER", 12),
    ],
}
path = source / "src/data/wild_encounters.json"
wild = json.loads(path.read_text(encoding="utf-8"))
seen = set()
for group in wild["wild_encounter_groups"]:
    if not group["for_maps"]:
        continue
    for area in group["encounters"]:
        map_id = area["map"]
        if map_id not in encounters:
            continue
        mons = area["land_mons"]["mons"]
        if len(mons) != len(encounters[map_id]):
            raise SystemExit(f"Unexpected land encounter count for {map_id}")
        for slot, (species, level) in zip(mons, encounters[map_id]):
            slot.update(species=f"SPECIES_{species}", min_level=level, max_level=level)
        seen.add(map_id)
if seen != encounters.keys():
    raise SystemExit("Some Lockmere encounter maps were not found")
path.write_text(json.dumps(wild, indent=2) + "\n", encoding="utf-8")
