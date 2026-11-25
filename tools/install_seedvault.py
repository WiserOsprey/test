#!/usr/bin/env python3
"""Install the Seedvault greenhouse, ferry, encounters and second gym."""
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from emerald_sprites import fit_sprite, index_sprite

source, assets = map(Path, sys.argv[1:3])
GYM = "data/maps/DewfordTown_Gym"
WIDTH, HEIGHT = 18, 28

# Each branch ends before a walkable wall or another mirror.
MIRRORS = {
    "A": ((3, 19), "west", "east"),
    "B": ((12, 19), "east", "north"),
    "C": ((12, 10), "north", "west"),
}
BRANCHES = {
    "A": [(x, 19) for x in range(1, 3)],
    "AB": [(x, 19) for x in range(4, 12)],
    "B": [(x, 19) for x in range(13, 17)],
    "BC": [(12, y) for y in range(11, 19)],
    "C": [(12, y) for y in range(7, 10)],
    "CR": [(x, 10) for x in range(8, 12)],
}
GATES = ((8, 6), (9, 6))
RECEIVER = (7, 10)
STATION = (13, 3)


def edit(path, transform):
    file = source / path
    file.write_text(transform(file.read_text(encoding="utf-8")), encoding="utf-8")


def substitute(text, before, after):
    if text.count(before) != 1:
        raise SystemExit(f"Expected one source match for {before[:85]!r}")
    return text.replace(before, after, 1)


def dialogue(text, label, lines):
    block = re.search(rf"(?m)^{label}:\n(?:\t\.string .+\n)+", text)
    if block is None:
        raise SystemExit(f"Missing text {label}")
    return substitute(text, block[0], label + ":\n" + "".join(f'\t.string "{line}"\n' for line in lines))


def read_json(path):
    return json.loads((source / path).read_text(encoding="utf-8"))


def write_json(path, parsed):
    (source / path).write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tile_art():
    shades = [
        (0, 0, 0), (20, 31, 34), (29, 51, 54), (43, 72, 72),
        (67, 96, 86), (95, 127, 101), (126, 161, 113), (178, 199, 139),
        (206, 222, 165), (102, 62, 41), (143, 96, 49), (184, 134, 69),
        (226, 174, 88), (249, 215, 130), (255, 243, 181), (232, 245, 227),
    ]
    tiles = {}

    def draw_tile(name, fill):
        tiles[name] = Image.new("P", (16, 16), fill)
        return ImageDraw.Draw(tiles[name])

    d = draw_tile("floor", 4)
    d.line((0, 15, 15, 15), fill=3)
    d.line((0, 7, 15, 7), fill=3)
    d.line((5, 0, 5, 6), fill=3)
    d.line((11, 8, 11, 14), fill=3)
    d.line((0, 8, 10, 8), fill=5)

    d = draw_tile("glass", 3)
    d.rectangle((2, 1, 13, 14), fill=5, outline=7)
    d.line((8, 2, 8, 13), fill=3)
    d.line((3, 7, 12, 7), fill=4)
    d.line((3, 5, 6, 2), fill=8)
    d.line((9, 12, 12, 9), fill=7)

    d = draw_tile("bed", 3)
    d.rectangle((1, 1, 14, 14), fill=9, outline=10)
    for x, y in ((5, 5), (10, 6), (5, 11), (11, 11)):
        d.line((x, y, x, y + 2), fill=7)
        d.point([(x - 1, y), (x + 1, y - 1)], fill=6)

    d = draw_tile("grille", 3)
    d.rectangle((1, 0, 14, 14), outline=11, fill=1)
    for x in (3, 6, 9, 12):
        d.line((x, 0, x, 13), fill=10)
    d.line((1, 6, 14, 6), fill=12)

    for key, vertical in (("ray_h", False), ("ray_v", True)):
        tiles[key] = tiles["floor"].copy()
        d = ImageDraw.Draw(tiles[key])
        for i in range(5, 11):
            d.line((i, 0, i, 15) if vertical else (0, i, 15, i),
                   fill=14 if 7 <= i <= 8 else 12)

    for name, direction in (("source", "north"), ("west", "west"), ("east", "east"), ("north", "north")):
        d = draw_tile(name, 4)
        d.rectangle((1, 1, 14, 14), fill=2, outline=11)
        d.polygon([(8, 3), (12, 8), (8, 12), (3, 8)], fill=10, outline=13)
        arrows = {"west": ((4, 8), (9, 5), (9, 11)),
                  "east": ((11, 8), (6, 5), (6, 11)),
                  "north": ((8, 4), (5, 9), (11, 9))}
        d.polygon(arrows[direction], fill=15 if name == "source" else 14)

    for name, bright in (("receiver", False), ("receiver_on", True), ("station", True)):
        d = draw_tile(name, 4)
        d.rectangle((1, 2, 14, 13), fill=2, outline=8 if bright else 5)
        d.rectangle((3, 4, 12, 10), fill=13 if name == "receiver_on" else 5 if bright else 3)
        d.point([(5, 6), (6, 7), (8, 7), (10, 5)], fill=15 if bright else 6)
        d.line((3, 12, 12, 12), fill=7)
    return shades, tiles


def install_tiles():
    directory = source / "data/tilesets/secondary/dewford_gym"
    shades, art = tile_art()
    sheet_file = directory / "tiles.png"
    with Image.open(sheet_file) as image:
        old = image.copy()
    if old.mode != "P" or old.width != 128 or old.height % 8 != 0:
        raise SystemExit("Unexpected Seedvault source tile sheet")
    count = old.width * old.height // 64
    sheet = Image.new("P", (128, old.height + 8 * ((4 * len(art) + 15) // 16)))
    sheet.putpalette(old.getpalette())
    sheet.paste(old, (0, 0))
    palette = directory / "palettes/12.pal"
    palette.write_text("JASC-PAL\n0100\n16\n" + "\n".join(
        " ".join(map(str, rgb)) for rgb in shades) + "\n", encoding="ascii")

    mt = directory / "metatiles.bin"
    at = directory / "metatile_attributes.bin"
    data = bytearray(mt.read_bytes())
    attrs = bytearray(at.read_bytes())
    if len(data) != 8 * len(attrs):
        raise SystemExit("Invalid Seedvault tile attributes")
    ids = {}
    for name, tile in art.items():
        ids[name] = 512 + len(data) // 16
        entries = []
        for y in (0, 8):
            for x in (0, 8):
                sheet.paste(tile.crop((x, y, x + 8, y + 8)), ((count % 16) * 8, (count // 16) * 8))
                entries.append((12 << 12) | (512 + count))
                count += 1
        data.extend(struct.pack("<8H", *entries, 0, 0, 0, 0))
        attrs.extend(b"\0\0")
    sheet.save(sheet_file, bits=4)
    mt.write_bytes(data)
    at.write_bytes(attrs)
    return ids


def define_room(ids):
    path = source / "data/layouts/DewfordTown_Gym/map.bin"
    grid = list(struct.unpack("<504H", path.read_bytes()))
    exits = {x: grid[27 * WIDTH + x] for x in (5, 6)}

    def place(x, y, tile, blocked=False):
        grid[y * WIDTH + x] = ids[tile] | 0x3000 | (0x400 if blocked else 0)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x in (0, 17) or y in (0, 1, 27):
                place(x, y, "glass", True)
            elif y == 6:
                place(x, y, "grille" if (x, y) in GATES else "glass", True)
            else:
                place(x, y, "floor")

    # Beds flank the center aisle without cutting across the mirrors or beams.
    for y in (3, 4, 8, 13, 14, 16, 23, 24):
        for x in (1, 2, 15, 16):
            place(x, y, "bed", True)
    for x in exits:
        grid[27 * WIDTH + x] = exits[x]
    for y in (20, 21, 22):
        place(3, y, "ray_v")
    place(3, 23, "source", True)
    for ((x, y), direction, _) in MIRRORS.values():
        place(x, y, direction, True)
    place(*RECEIVER, "receiver", True)
    place(*STATION, "station", True)
    path.write_bytes(struct.pack("<504H", *grid))

    map_path = f"{GYM}/map.json"
    events = read_json(map_path)
    positions = {
        "Brawly": (8, 3), "GymGuide": (7, 25), "Takao": (5, 22),
        "Jocelyn": (14, 21), "Laura": (8, 17), "Brenden": (5, 13),
        "Cristian": (10, 9), "Lilith": (13, 14),
    }
    for item in events["object_events"]:
        item["x"], item["y"] = positions[item["script"].rsplit("_", 1)[-1]]
        item.update(elevation=3, movement_type="MOVEMENT_TYPE_FACE_DOWN",
                    movement_range_x=0, movement_range_y=0)
        if item["trainer_type"] == "TRAINER_TYPE_NORMAL":
            item["trainer_sight_or_berry_tree_id"] = "1"
    events["bg_events"] = []
    for (x, y), interaction in [
        *((pos, f"Seedvault_TurnMirror{letter}") for letter, (pos, _, _) in MIRRORS.items()),
        (RECEIVER, "Seedvault_CheckReceiver"), (STATION, "Seedvault_FieldStation"),
    ]:
        events["bg_events"].append({
            "type": "sign", "x": x, "y": y, "elevation": 0,
            "player_facing_dir": "BG_EVENT_PLAYER_FACING_NORTH", "script": interaction,
        })
    write_json(map_path, events)


def make_beam_scripts(ids):
    def tile(points, name, solid=0):
        return "".join(f"\tsetmetatile {x}, {y}, 0x{ids[name]:03X}, {solid}\n" for x, y in points)

    def variant(letter):
        pos, left, right = MIRRORS[letter]
        return (
            f"Seedvault_Aim{letter}:\n"
            f"\tgoto_if_eq VAR_SEEDVAULT_{letter}, 1, Seedvault_Aim{letter}Active\n"
            + tile([pos], left, 1) + "\treturn\n\n"
            f"Seedvault_Aim{letter}Active:\n"
            + tile([pos], right, 1) + "\treturn\n\n"
        )

    scripts = "Seedvault_TraceLight:\n\tsetvar VAR_SEEDVAULT_LIT, 0\n"
    for coords in BRANCHES.values():
        scripts += tile(coords, "floor")
    scripts += tile(GATES, "grille", 1) + tile([RECEIVER], "receiver", 1)
    scripts += "".join(f"\tcall Seedvault_Aim{letter}\n" for letter in MIRRORS)
    scripts += "\tgoto_if_eq VAR_SEEDVAULT_A, 0, Seedvault_MissA\n" + tile(BRANCHES["AB"], "ray_h")
    scripts += "\tgoto_if_eq VAR_SEEDVAULT_B, 0, Seedvault_MissB\n" + tile(BRANCHES["BC"], "ray_v")
    scripts += "\tgoto_if_eq VAR_SEEDVAULT_C, 0, Seedvault_MissC\n" + tile(BRANCHES["CR"], "ray_h")
    scripts += tile([RECEIVER], "receiver_on", 1) + tile(GATES, "floor")
    scripts += "\tsetvar VAR_SEEDVAULT_LIT, 1\n\treturn\n\n"
    for letter, beam in (("A", "ray_h"), ("B", "ray_h"), ("C", "ray_v")):
        scripts += f"Seedvault_Miss{letter}:\n" + tile(BRANCHES[letter], beam) + "\treturn\n\n"
    return scripts + "".join(variant(letter) for letter in MIRRORS)


def install_gym_scripts(ids):
    helper = Path(__file__).with_name("seedvault_lights.inc").read_text(encoding="utf-8")

    def apply(text):
        text = substitute(text,
            "DewfordTown_Gym_OnTransition:\n\tcall DewfordTown_Gym_EventScript_SetFlashLevel\n\tend",
            "DewfordTown_Gym_OnTransition:\n\tsetflashlevel 0\n"
            "\tcall_if_set FLAG_BADGE02_GET, Seedvault_PrepareClearedRoom\n"
            "\tcall Seedvault_TraceLight\n\tend")
        text = substitute(text, "DewfordTown_Gym_EventScript_Brawly::\n",
            "DewfordTown_Gym_EventScript_Brawly::\n"
            "\tgoto_if_eq VAR_SEEDVAULT_LIT, 0, Seedvault_ServiceExit\n")
        text = substitute(text, "\tcall DewfordTown_Gym_EventScript_AnimateFlashFullBrightness\n", "")
        for name in ("Takao", "Jocelyn", "Laura", "Brenden", "Cristian", "Lilith"):
            callback = f"DewfordTown_Gym_EventScript_{name}BrightenRoom"
            text = substitute(text, f"Defeat, {callback}\n", "Defeat\n")
        text = text.replace("giveitem ITEM_TM_BULK_UP", "giveitem ITEM_TM_GIGA_DRAIN")
        for label, lines in GYM_TEXT.items():
            text = dialogue(text, "DewfordTown_Gym_Text_" + label, lines)
        return text + "\n" + helper + "\n" + make_beam_scripts(ids)

    edit(f"{GYM}/scripts.inc", apply)


GYM_TEXT = {
    "GymGuideAdvice": [r"The roof is open, but the light is",
                       r"missing the germination receiver.\p",
                       r"Turn three mirrors so the beam runs",
                       r"from the skylight to the green box.\p",
                       r"PELL uses BUG types. Use FIRE or",
                       r"FLYING moves against the leaf wings.$"],
    "GymGuidePostVictory": [r"Those buds opened right on schedule.", r"Keep an eye on the west seed beds.$"],
    "BrawlyIntro": [r"PELL: The receiver is awake again.\p",
                    r"GRAFTWING waits for a certain light",
                    r"before it opens the seed pods.\p",
                    r"Let's see how well you and your",
                    r"partners read a change in conditions.$"],
    "BrawlyDefeat": [r"PELL: Your partners adapted faster",
                      r"than the light could move.\p",
                      r"Take the KNUCKLE BADGE. You earned it.$"],
    "ReceivedKnuckleBadge": [r"{PLAYER} received the KNUCKLE BADGE",
                             r"from PELL.$"],
    "KnuckleBadgeInfoTakeThis": [r"With the KNUCKLE BADGE you can use",
                                  r"FLASH outside of battle.\p",
                                  r"It also helps traded POKéMON up to",
                                  r"level 30 listen to you.\p",
                                  r"Take a greenhouse TM, too.$"],
    "ExplainBulkUp": [r"TM19 contains GIGA DRAIN.",
                      r"It draws strength from the target.\p",
                      r"I learned it watching the seedlings",
                      r"share a bench with GRAFTWING.$"],
    "RegisteredBrawly": [r"Registered GYM LEADER PELL",
                          r"in the POKéNAV.$"],
    "BrawlyPostBattle": [r"Use the field station by the east wall",
                          r"to try the greenhouse experiments.\p",
                          r"A relay still flickers above the",
                          r"KITEWATCH shelves. They're next.$"],
    "GymStatue": [r"SEEDVAULT GYM\p", r"LEADER: PELL",
                   r"GREENHOUSE LIGHT SURVEY$"],
    "GymStatueCertified": [r"SEEDVAULT GYM\p", r"CERTIFIED SURVEYOR: {PLAYER}$"],
    "BrawlyPreRematch": [r"PELL: A new clutch has hatched.",
                           r"Would you help me track its progress?$"],
    "BrawlyRematchDefeat": [r"This proves I need a longer logbook.$"],
    "BrawlyPostRematch": [r"PELL: I can already see which seedlings",
                            r"will need a different bench.$"],
    "BrawlyRematchNeedTwoMons": [r"PELL: Bring two partners so we can",
                                    r"compare their work side by side.$"],
}
for trainer in ("Takao", "Jocelyn", "Laura", "Brenden", "Cristian", "Lilith"):
    GYM_TEXT.update({
        trainer + "Intro": [r"The beds need observation first.",
                            r"Show me how you read your partners!$"],
        trainer + "Defeat": [r"You noticed the change before I did.$"],
        trainer + "PostBattle": [r"Follow the bright line between",
                                 r"mirrors until it meets the receiver.$"],
    })


def fix_text_rows(records):
    # Each source line except the final one needs a line break, continuation or page.
    for name, rows in records.items():
        for i, line in enumerate(rows[:-1]):
            if not line.endswith((r"\n", r"\l", r"\p")):
                rows[i] = line + r"\n"


fix_text_rows(GYM_TEXT)
ids = install_tiles()
define_room(ids)
install_gym_scripts(ids)

def use_vars(text):
    for suffix, label in (("FA", "A"), ("FB", "B"), ("FC", "C"), ("FD", "LIT")):
        before = f"VAR_UNUSED_0x40{suffix}                                0x40{suffix} // Unused Var"
        text = substitute(text, before, f"VAR_SEEDVAULT_{label:<35} 0x40{suffix}")
    return text

edit("include/constants/vars.h", use_vars)


def install_teams():
    def edit_trainers(text):
        name = '.trainerName = _("BRAWLY"),'
        if name not in text:
            raise SystemExit("Missing Seedvault gym leader")
        return text.replace(name, '.trainerName = _("PELL"),')

    edit("src/data/trainers.h", edit_trainers)
    teams = {
        "Takao": ("SHROOMISH", 14), "Jocelyn": ("WURMPLE", 14),
        "Laura": ("SILCOON", 14), "Brenden": ("BRELOOM", 16),
        "Cristian": ("BEAUTIFLY", 16), "Lilith": ("BRELOOM", 16),
    }

    def edit_parties(text):
        for name, (species, level) in teams.items():
            pat = rf"(?ms)^(static const struct TrainerMonNoItemDefaultMoves sParty_{name}\[\] = \{{).*?^\}};"
            replacement = (
                f"\n    {{.iv = 120, .lvl = {level}, .species = SPECIES_{species}}}\n"
                "};"
            )
            text, count = re.subn(pat, lambda m: m[1] + replacement, text, count=1)
            if count != 1:
                raise SystemExit(f"Missing party for {name}")

        party = """static const struct TrainerMonItemCustomMoves sParty_Brawly1[] = {
    {
        .iv = 110, .lvl = 17, .species = SPECIES_BEAUTIFLY, .heldItem = ITEM_NONE,
        .moves = {MOVE_SILVER_WIND, MOVE_METAL_CLAW, MOVE_STRING_SHOT, MOVE_PROTECT}
    },
    {
        .iv = 125, .lvl = 18, .species = SPECIES_BRELOOM, .heldItem = ITEM_NONE,
        .moves = {MOVE_FURY_CUTTER, MOVE_MEGA_DRAIN, MOVE_STUN_SPORE, MOVE_GROWTH}
    },
    {
        .iv = 150, .lvl = 21, .species = SPECIES_HERACROSS, .heldItem = ITEM_SITRUS_BERRY,
        .moves = {MOVE_SILVER_WIND, MOVE_MEGA_DRAIN, MOVE_GUST, MOVE_SUNNY_DAY}
    }
};"""
        text, count = re.subn(r"(?ms)^static const struct TrainerMonItemCustomMoves sParty_Brawly1\[\] = \{.*?^\};",
                              lambda _: party, text, count=1)
        if count != 1:
            raise SystemExit("Missing Pell's party")
        return text

    edit("src/data/trainer_parties.h", edit_parties)

    sprite = fit_sprite(assets / "pell.png")
    visible = [pixel[:3] for pixel in sprite.getdata() if pixel[3]]
    sample = Image.new("RGB", (len(visible), 1))
    sample.putdata(visible)
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = quantized.getpalette()[:45]
    colors = [(0, 0, 0), *(tuple(palette[i:i + 3]) for i in range(0, 45, 3))]
    index_sprite(sprite, colors).save(source / "graphics/trainers/front_pics/leader_brawly.png",
                                     bits=4, transparency=0)


def install_ferry():
    for town, npc in (("RustboroCity", "Man1"), ("DewfordTown", "Woman")):
        path = f"data/maps/{town}/map.json"
        events = read_json(path)
        script = f"{town}_EventScript_{npc}"
        operator = next(event for event in events["object_events"] if event["script"] == script)
        operator.update(script=f"Seedvault_Ferry_{town}", movement_type="MOVEMENT_TYPE_FACE_DOWN",
                        movement_range_x=0, movement_range_y=0)
        write_json(path, events)

    def ferry_script(town, destination, x, y, arrival, require_badge):
        gate = ("\tgoto_if_unset FLAG_BADGE01_GET, Seedvault_Ferry_LockmereClosed\n"
                if require_badge else "")
        return (
            f"\nSeedvault_Ferry_{town}::\n\tlock\n\tfaceplayer\n"
            + gate + f"\tmsgbox Seedvault_Text_Ferry_{town}, MSGBOX_YESNO\n"
            f"\tgoto_if_eq VAR_RESULT, NO, Seedvault_Ferry_{town}_End\n"
            f"\twarp {destination}, {x}, {y}\n\twaitstate\n"
            f"Seedvault_Ferry_{town}_End:\n\trelease\n\tend\n\n"
            f"Seedvault_Text_Ferry_{town}:\n"
            '\t.string "I run the survey ferry.\\p"\n'
            f'\t.string "Set out for {arrival}?$"\n'
        )

    closed = """
Seedvault_Ferry_LockmereClosed:
	msgbox Seedvault_Text_FerryLocked, MSGBOX_DEFAULT
	release
	end

Seedvault_Text_FerryLocked:
	.string "The crossing is closed while the lock"
	.string "\\ncrew works. Ask TAMSIN at the GYM.$"
"""
    edit("data/maps/RustboroCity/scripts.inc",
         lambda text: text + ferry_script("RustboroCity", "MAP_DEWFORD_TOWN", 7, 13, "SEEDVAULT", True) + closed)
    edit("data/maps/DewfordTown/scripts.inc",
         lambda text: text + ferry_script("DewfordTown", "MAP_RUSTBORO_CITY", 26, 24, "LOCKMERE", False))

    edit("data/maps/RustboroCity_Gym/scripts.inc",
         lambda text: dialogue(text, "RustboroCity_Gym_Text_RoxannePostBattle", [
             r"PELL saw the same flicker at SEEDVAULT.\p",
             r"The ferry operator is just south\n",
             r"of this GYM. Now that the lock's open,\l",
             r"you can take the survey ferry.$",
         ]))


def install_district():
    def signs(text):
        signs = {
            "TownSign": [r"SEEDVAULT\p", r"The seed keepers' island.$"],
            "GymSign": [r"SEEDVAULT GREENHOUSE GYM\p", r"LEADER: PELL\n", r"BUG TYPE CERTIFICATION$"],
            "HallSign": [r"SEEDVAULT TOWN HALL\n", r"Seed records and ferry schedules.$"],
        }
        for name, lines in signs.items():
            text = dialogue(text, "DewfordTown_Text_" + name, lines)
        return text

    edit("data/maps/DewfordTown/scripts.inc", signs)
    path = "src/data/region_map/region_map_sections.json"
    data = read_json(path)
    for area in data["map_sections"]:
        if area["id"] == "MAPSEC_DEWFORD_TOWN":
            area["name"] = "SEEDVAULT"
        if area["id"] == "MAPSEC_GRANITE_CAVE":
            area["name"] = "GLASSROOT TUNNEL"
    write_json(path, data)

    path = "src/data/wild_encounters.json"
    data = read_json(path)
    replacements = {
        "MAP_GRANITE_CAVE_1F": [
            ("SHROOMISH", 9), ("WURMPLE", 9), ("SHROOMISH", 10), ("ZIGZAGOON", 11),
            ("GEODUDE", 10), ("SHROOMISH", 11), ("GEODUDE", 11), ("SILCOON", 11),
            ("SHROOMISH", 12), ("ZIGZAGOON", 12), ("MUDKIP", 11), ("BRELOOM", 13),
        ],
        "MAP_GRANITE_CAVE_B1F": [
            ("SHROOMISH", 12), ("GEODUDE", 12), ("SHROOMISH", 13), ("SILCOON", 12),
            ("SHROOMISH", 14), ("GEODUDE", 13), ("ZIGZAGOON", 13), ("BRELOOM", 15),
            ("GRAVELER", 14), ("SHROOMISH", 14), ("BRELOOM", 15), ("BRELOOM", 16),
        ],
        "MAP_GRANITE_CAVE_B2F": [
            ("GEODUDE", 13), ("SHROOMISH", 13), ("SHROOMISH", 14), ("GEODUDE", 14),
            ("SHROOMISH", 15), ("SILCOON", 14), ("ZIGZAGOON", 14), ("BRELOOM", 16),
            ("BRELOOM", 17), ("GRAVELER", 16), ("BRELOOM", 17), ("HERACROSS", 20),
        ],
    }
    seen = set()
    for group in data["wild_encounter_groups"]:
        for area in group["encounters"]:
            key = area.get("map")
            if key not in replacements:
                continue
            mons = area["land_mons"]["mons"]
            if len(mons) != len(replacements[key]):
                raise SystemExit(f"Unexpected encounter count for {key}")
            for slot, (species, level) in zip(mons, replacements[key]):
                slot.update(species=f"SPECIES_{species}", min_level=level, max_level=level)
            seen.add(key)
    if seen != replacements.keys():
        raise SystemExit("Could not find all Glassroot encounter maps")
    write_json(path, data)


install_teams()
install_ferry()
install_district()
