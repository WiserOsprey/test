#!/usr/bin/env python3
"""Install Kitewatch's ridge gym, survey ferries, and regional encounters."""
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from reedwake_district_assets import append_district_tiles, install_trainer_art

source, assets = map(Path, sys.argv[1:3])
GYM = "data/maps/MauvilleCity_Gym"
WIDTH, HEIGHT = 10, 21

WEST, EAST = (2, 3), (6, 7)
CROSSINGS = (15, 11, 7)
DIALS = ((4, 17), (4, 13), (4, 9))
STATION = (7, 3)

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
    palette = [
        (0, 0, 0), (18, 22, 39), (29, 35, 59), (45, 53, 79),
        (63, 78, 98), (88, 105, 128), (114, 137, 151), (154, 176, 184),
        (196, 221, 216), (77, 55, 57), (128, 90, 64), (169, 120, 73),
        (211, 158, 86), (250, 197, 107), (105, 193, 208), (236, 225, 174),
    ]
    tiles = {}

    def tile(name, background):
        tiles[name] = Image.new("P", (16, 16), background)
        return ImageDraw.Draw(tiles[name])

    draw = tile("shelf", 5)
    draw.line((0, 0, 15, 0), fill=6)
    draw.line((0, 15, 15, 15), fill=4)
    draw.line((4, 5, 6, 7, 9, 7), fill=4)
    draw.point([(2, 4), (10, 12), (13, 5), (4, 13)], fill=6)

    draw = tile("rim", 3)
    draw.rectangle((1, 1, 14, 13), outline=5, fill=4)
    draw.line((2, 1, 13, 1), fill=7)
    draw.line((2, 12, 13, 12), fill=2)
    draw.point([(3, 4), (11, 4), (3, 10), (11, 10)], fill=6)

    draw = tile("windbreak", 4)
    draw.rectangle((0, 0, 15, 14), outline=3, fill=6)
    draw.line((1, 2, 14, 2), fill=8)
    draw.line((2, 6, 13, 6), fill=5)
    draw.line((6, 3, 6, 5), fill=4)
    draw.line((11, 7, 11, 13), fill=4)
    draw.line((0, 15, 15, 15), fill=3)

    draw = tile("sky", 2)
    for x, y, end in ((1, 3, 8), (9, 7, 15), (0, 11, 10)):
        draw.line((x, y, end, y), fill=4)
        draw.point((end - 2, y - 1), fill=5)

    draw = tile("bridge", 2)
    draw.rectangle((1, 0, 14, 15), fill=10, outline=9)
    for y in (1, 5, 9, 13):
        draw.line((3, y, 12, y), fill=12)
        draw.line((3, y + 2, 12, y + 2), fill=9)
    for x in (1, 14):
        draw.line((x, 0, x, 15), fill=14)
        draw.point([(x, 2), (x, 13)], fill=15)

    for name, west in (("dial_w", True), ("dial_e", False)):
        draw = tile(name, 5)
        draw.rectangle((1, 2, 14, 14), fill=3, outline=10)
        draw.rectangle((3, 4, 12, 10), fill=2, outline=7)
        draw.line((4, 7, 11, 7), fill=14)
        if west:
            draw.polygon(((3, 7), (7, 4), (7, 10)), fill=15)
        else:
            draw.polygon(((12, 7), (8, 4), (8, 10)), fill=15)
        draw.point([(4, 12), (11, 12)], fill=13)

    draw = tile("station", 5)
    draw.rectangle((2, 1, 13, 14), fill=3, outline=10)
    draw.rectangle((4, 3, 11, 8), fill=2, outline=7)
    draw.line((5, 7, 6, 5, 8, 7, 10, 4), fill=14)
    draw.point([(5, 11), (8, 11), (10, 11)], fill=13)
    return palette, tiles


def install_ridge(ids):
    path = source / "data/layouts/MauvilleCity_Gym/map.bin"
    grid = list(struct.unpack("<210H", path.read_bytes()))
    exits = {x: grid[20 * WIDTH + x] for x in (4, 5)}

    def place(x, y, name, solid=False):
        grid[y * WIDTH + x] = ids[name] | 0x3000 | (0x400 if solid else 0)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x in (0, 9) or y in (0, 1, 20):
                place(x, y, "rim", True)
            elif y in CROSSINGS:
                place(x, y, "bridge" if x in EAST else "sky", x not in EAST)
            else:
                place(x, y, "shelf")

    # Every bridge follows the gust across its gap. Staggered windbreaks
    # determine which side offers a landing on the next terrace.
    for row, blocked_side in ((14, EAST), (10, WEST), (6, EAST)):
        for x in blocked_side:
            place(x, row, "windbreak", True)

    for x, y in DIALS:
        place(x, y, "dial_e", True)
    place(*STATION, "station", True)
    for x, code in exits.items():
        grid[20 * WIDTH + x] = code
    path.write_bytes(struct.pack("<210H", *grid))

    events_path = f"{GYM}/map.json"
    events = read_json(events_path)
    positions = {
        "Wattson": (4, 3), "Shawn": (1, 9), "Vivian": (7, 18), "Ben": (1, 13),
        "Kirk": (8, 13), "GymGuide": (2, 18), "Angelo": (8, 5),
    }
    for npc in events["object_events"]:
        name = npc["script"].rsplit("_", 1)[-1]
        npc["x"], npc["y"] = positions[name]
        npc.update(elevation=3, movement_type="MOVEMENT_TYPE_FACE_DOWN",
                   movement_range_x=0, movement_range_y=0)
        if name == "Wattson":
            npc["flag"] = "0"
        if npc["trainer_type"] == "TRAINER_TYPE_NORMAL":
            npc["trainer_sight_or_berry_tree_id"] = "1"

    events["coord_events"] = []
    events["bg_events"] = [{
        "type": "sign", "x": x, "y": y, "elevation": 0,
        "player_facing_dir": "BG_EVENT_PLAYER_FACING_NORTH", "script": label,
    } for (x, y), label in (
        *((pos, "Kitewatch_TurnDial") for pos in DIALS),
        (STATION, "Kitewatch_FieldStation"),
    )]
    write_json(events_path, events)


def wind_scripts(ids):
    def tile(x, y, name, solid):
        return f"\tsetmetatile {x}, {y}, 0x{ids[name]:03X}, {int(solid)}\n"

    paths = (
        ("East", (EAST, EAST, EAST), "dial_e"),
        ("West", (WEST, WEST, WEST), "dial_w"),
        ("Parked", (WEST, EAST, WEST), "dial_w"),
    )
    text = (
        "Kitewatch_ApplyWind:\n"
        "\tgoto_if_set FLAG_BADGE03_GET, Kitewatch_WindParked\n"
        "\tgoto_if_eq VAR_KITEWATCH_WIND, 1, Kitewatch_WindWest\n"
        "\tgoto Kitewatch_WindEast\n\n"
    )
    for name, crossings, dial in paths:
        text += f"Kitewatch_Wind{name}:\n"
        for y, active in zip(CROSSINGS, crossings):
            for x in WEST + EAST:
                text += tile(x, y, "bridge" if x in active else "sky", x not in active)
        for x, y in DIALS:
            text += tile(x, y, dial, True)
        text += "\treturn\n\n"
    return text

GYM_DIALOGUE = {
    "GymGuideAdvice": [
        r"The platforms move together. Turn a",
        r"dial to shift them east or west.",
        r"The stone windbreaks block some",
        r"landings. Change wind at each shelf.\p",
        r"VENN uses FLYING types. Bring ROCK,",
        r"ICE, or ELECTRIC moves.$",
    ],
    "GymGuidePostVictory": [r"The platforms are docked now.",
                             r"Take a minute to look at the clouds.$"],
    "WattsonIntro": [r"VENN: You found the lee of each shelf.\p",
                     r"GALEGULL reads those same shifts",
                     r"by opening its forked tail.",
                     r"Let's see how your team responds",
                     r"when the air starts moving.$"],
    "WattsonDefeat": [r"VENN: You found a clean line through",
                       r"that gust. Nicely flown.\p",
                       r"The DYNAMO BADGE is yours.$"],
    "ReceivedDynamoBadge": [r"{PLAYER} received the DYNAMO BADGE",
                              r"from VENN.$"],
    "ExplainDynamoBadgeTakeThis": [r"The DYNAMO BADGE lets you use ROCK",
                                    r"SMASH outside of battle.\p",
                                    r"Take a move I teach young gliders.$"],
    "ExplainShockWave": [r"TM40 contains AERIAL ACE.",
                          r"It's a FLYING move that keeps its",
                          r"aim when the target is evasive.$"],
    "RegisteredWattson": [r"Registered GYM LEADER VENN",
                            r"in the POKéNAV.$"],
    "WattsonPostBattle": [r"The field station is open now.\p",
                           r"A relay in COILMARKET is drawing",
                           r"more current than it can shed.",
                           r"Keep that in your notebook.$"],
    "WattsonGoForthAndEndeavor": [r"Thanks for following that signal.",
                                   r"The ridge can breathe again.$"],
    "GymStatue": [r"KITEWATCH GYM\p", r"LEADER: VENN", r"RIDGE WIND SURVEY$"],
    "GymStatueCertified": [r"KITEWATCH GYM\p", r"CERTIFIED SURVEYOR: {PLAYER}$"],
    "WattsonPreRematch": [r"VENN: Today's wind feels different.",
                           r"Care to see what it does to a battle?$"],
    "WattsonRematchDefeat": [r"I missed the shift in that one!$"],
    "WattsonPostRematch": [r"VENN: Good work. I'll try that line",
                            r"next time I check the ridge.$"],
    "WattsonRematchNeedTwoMons": [r"VENN: Bring two partners so I can",
                                    r"read the gusts between them.$"],
}
for trainer in ("Shawn", "Vivian", "Ben", "Kirk", "Angelo"):
    GYM_DIALOGUE.update({
        trainer + "Intro": [r"The ridge has its own rhythm.",
                            r"Let's see if your team can read it!$"],
        trainer + "Defeat": [r"I leaned into that gust too late.$"],
        trainer + "PostBattle": [r"Look across the next gap before",
                                 r"you turn the wind dial.$"],
    })


def install_gym(ids):
    helper = Path(__file__).with_name("kitewatch_wind.inc").read_text(encoding="utf-8")

    def apply(text):
        text = substitute(text, "\tmap_script MAP_SCRIPT_ON_LOAD, MauvilleCity_Gym_OnLoad\n",
                          "\tmap_script MAP_SCRIPT_ON_TRANSITION, Kitewatch_OnTransition\n")
        text = substitute(text, "MauvilleCity_Gym_EventScript_Wattson::\n",
            "MauvilleCity_Gym_EventScript_Wattson::\n"
            "\tgoto_if_unset FLAG_BADGE02_GET, Kitewatch_ReturnToEntrance\n")
        text = substitute(text,
            "\tspecial MauvilleGymDeactivatePuzzle\n\tspecial DrawWholeMapView\n",
            "\tcall Kitewatch_ApplyWind\n\tspecial DrawWholeMapView\n")
        text = text.replace("giveitem ITEM_TM_SHOCK_WAVE", "giveitem ITEM_TM_AERIAL_ACE")
        for label, lines in GYM_DIALOGUE.items():
            rows = [line + r"\n" if i < len(lines) - 1 and not line.endswith((r"\p", r"\n", r"\l"))
                    else line for i, line in enumerate(lines)]
            text = dialogue(text, "MauvilleCity_Gym_Text_" + label, rows)
        return (
            text + "\nKitewatch_OnTransition:\n\tcall Kitewatch_ApplyWind\n\tend\n\n"
            + helper + "\n" + wind_scripts(ids)
        )

    edit(f"{GYM}/scripts.inc", apply)


def install_teams():
    def trainers(text):
        pattern = r"(?ms)^    \[TRAINER_WATTSON_[1-5]\] =\n    \{.*?^    \},"
        text, count = re.subn(pattern, lambda m:
            m[0].replace('.trainerName = _("WATTSON"),', '.trainerName = _("VENN"),')
                .replace(".encounterMusic_gender = TRAINER_ENCOUNTER_MUSIC_MALE,",
                         ".encounterMusic_gender = F_TRAINER_FEMALE | TRAINER_ENCOUNTER_MUSIC_FEMALE,"),
            text)
        if count != 5:
            raise SystemExit(f"Expected five Venn trainer records, found {count}")
        return text

    edit("src/data/trainers.h", trainers)
    lineups = {
        "Shawn": [("SWELLOW", 22, ())],
        "Vivian": [("TAILLOW", 19, ("PECK", "GROWL", "QUICK_ATTACK", "NONE"))],
        "Ben": [("LINOONE", 21, ("WING_ATTACK", "QUICK_ATTACK", "GUST", "NONE"))],
        "Kirk": [("TAILLOW", 20, ("WING_ATTACK", "QUICK_ATTACK", "GROWL", "NONE")),
                 ("SWELLOW", 22, ("GUST", "AERIAL_ACE", "QUICK_ATTACK", "NONE"))],
        "Angelo": [("SKARMORY", 22, ("WING_ATTACK", "WATER_GUN", "QUICK_ATTACK", "NONE"))],
        "Wattson1": [
            ("LINOONE", 23, ("AERIAL_ACE", "QUICK_ATTACK", "GUST", "SAND_ATTACK")),
            ("SWELLOW", 25, ("AERIAL_ACE", "QUICK_ATTACK", "WING_ATTACK", "AGILITY")),
            ("TROPIUS", 27, ("WATER_PULSE", "WING_ATTACK", "AERIAL_ACE", "AGILITY")),
        ],
    }

    def parties(text):
        for trainer, party in lineups.items():
            pat = rf"(?ms)^static const struct (TrainerMon\w+) sParty_{trainer}\[\] = \{{.*?^\}};"
            match = re.search(pat, text)
            if match is None:
                raise SystemExit(f"Missing party for {trainer}")
            struct_type = match[1]
            records = []
            for species, level, moves in party:
                item = "SITRUS_BERRY" if trainer == "Wattson1" and species == "TROPIUS" else "NONE"
                fields = [f".iv = 130, .lvl = {level}, .species = SPECIES_{species}"]
                if struct_type.startswith("TrainerMonItem"):
                    fields.append(f".heldItem = ITEM_{item}")
                if struct_type.endswith("CustomMoves"):
                    fields.append(".moves = {" + ", ".join(f"MOVE_{m}" for m in moves) + "}")
                records.append("    {" + ", ".join(fields) + "},")
            replacement = (f"static const struct {struct_type} sParty_{trainer}[] = {{\n"
                           + "\n".join(records) + "\n};")
            text = substitute(text, match[0], replacement)
        return text

    edit("src/data/trainer_parties.h", parties)
    install_trainer_art(assets / "venn.png", source / "graphics/trainers/front_pics/leader_wattson.png")


def install_ferries():
    seed_path = "data/maps/DewfordTown/map.json"
    seed = read_json(seed_path)
    seed["object_events"].append({
        "graphics_id": "OBJ_EVENT_GFX_SAILOR", "x": 10, "y": 12, "elevation": 3,
        "movement_type": "MOVEMENT_TYPE_FACE_DOWN", "movement_range_x": 0,
        "movement_range_y": 0, "trainer_type": "TRAINER_TYPE_NONE",
        "trainer_sight_or_berry_tree_id": "0", "script": "Kitewatch_FerrySeedvault", "flag": "0",
    })
    write_json(seed_path, seed)

    kite_path = "data/maps/MauvilleCity/map.json"
    kite = read_json(kite_path)
    operator = next(npc for npc in kite["object_events"] if npc["script"] == "MauvilleCity_EventScript_Maniac")
    operator.update(graphics_id="OBJ_EVENT_GFX_SAILOR", movement_type="MOVEMENT_TYPE_FACE_RIGHT",
                    movement_range_x=0, movement_range_y=0, script="Kitewatch_FerryTown")
    write_json(kite_path, kite)

    for town, label, gate, target, where, x, y in (
        ("DewfordTown", "Seedvault", True, "MAP_MAUVILLE_CITY", "KITEWATCH", 15, 11),
        ("MauvilleCity", "Town", False, "MAP_DEWFORD_TOWN", "SEEDVAULT", 10, 13),
    ):
        script = f"\nKitewatch_Ferry{label}::\n\tlock\n\tfaceplayer\n"
        if gate:
            script += "\tgoto_if_unset FLAG_BADGE02_GET, Kitewatch_FerryHold\n"
        script += (
            f"\tmsgbox Kitewatch_Text_Ferry{label}, MSGBOX_YESNO\n"
            f"\tgoto_if_eq VAR_RESULT, NO, Kitewatch_Ferry{label}End\n"
            f"\twarp {target}, {x}, {y}\n\twaitstate\n"
            f"Kitewatch_Ferry{label}End:\n\trelease\n\tend\n\n"
            f"Kitewatch_Text_Ferry{label}:\n"
            f'\t.string "I run the ridge ferry.\\p"\n\t.string "Set out for {where}?$"\n'
        )
        if gate:
            script += (
                "\nKitewatch_FerryHold:\n\tmsgbox Kitewatch_Text_FerryHold, MSGBOX_DEFAULT\n"
                "\trelease\n\tend\n\nKitewatch_Text_FerryHold:\n"
                '\t.string "Only certified surveyors can ride\\n"\n'
                '\t.string "the ridge ferry. Ask PELL at the GYM.$"\n'
            )
        edit(f"data/maps/{town}/scripts.inc", lambda text: text + script)

    edit("data/maps/DewfordTown_Gym/scripts.inc", lambda text:
        dialogue(text, "DewfordTown_Gym_Text_BrawlyPostBattle", [
            r"The eastern field station is open.\p",
            r"A relay flickers above KITEWATCH.\n",
            r"Take the ridge ferry from town.$",
        ]))


def install_district():
    def signs(text):
        for name, rows in {
            "CitySign": [r"KITEWATCH\p", r"The town above the crosswinds.$"],
            "GymSign": [r"KITEWATCH RIDGE GYM\p", r"LEADER: VENN\n", r"FLYING TYPE CERTIFICATION$"],
        }.items():
            text = dialogue(text, "MauvilleCity_Text_" + name, rows)
        return text

    edit("data/maps/MauvilleCity/scripts.inc", signs)
    path = "src/data/region_map/region_map_sections.json"
    region = read_json(path)
    names = {
        "MAPSEC_MAUVILLE_CITY": "KITEWATCH",
        "MAPSEC_ROUTE_110": "TIDEBREAK PASS",
        "MAPSEC_ROUTE_117": "LEEWARD SHELF",
        "MAPSEC_ROUTE_118": "GALE RUN",
    }
    for area in region["map_sections"]:
        if area["id"] in names:
            area["name"] = names[area["id"]]
    write_json(path, region)

    path = "src/data/wild_encounters.json"
    data = read_json(path)
    replacements = {
        "MAP_ROUTE110": [
            ("TAILLOW", 14), ("POOCHYENA", 16), ("TAILLOW", 15), ("GEODUDE", 15),
            ("SHROOMISH", 14), ("TAILLOW", 16), ("WURMPLE", 14), ("LINOONE", 16),
            ("SILCOON", 15), ("GRAVELER", 16), ("MUDKIP", 15), ("SWELLOW", 18),
        ],
        "MAP_ROUTE117": [
            ("TAILLOW", 17), ("GEODUDE", 16), ("SHROOMISH", 16), ("TAILLOW", 18),
            ("LINOONE", 17), ("POOCHYENA", 16), ("WURMPLE", 16), ("GRAVELER", 18),
            ("GEODUDE", 18), ("BRELOOM", 19), ("GRAVELER", 20), ("SWELLOW", 20),
        ],
        "MAP_ROUTE118": [
            ("TAILLOW", 18), ("GEODUDE", 18), ("LINOONE", 19), ("TAILLOW", 20),
            ("SHROOMISH", 18), ("WURMPLE", 18), ("SILCOON", 19), ("BRELOOM", 21),
            ("GRAVELER", 22), ("TAILLOW", 20), ("SWELLOW", 23), ("TROPIUS", 26),
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
        raise SystemExit("Missing Kitewatch encounter map")
    write_json(path, data)


edit("include/constants/vars.h", lambda text:
    substitute(text, "VAR_UNUSED_0x40FE                                0x40FE // Unused Var",
                     "VAR_KITEWATCH_WIND                               0x40FE"))
palette, art = tile_art()
ids = append_district_tiles(source / "data/tilesets/secondary/mauville_gym", palette, art)
install_ridge(ids)
install_gym(ids)
install_teams()
install_ferries()
install_district()
