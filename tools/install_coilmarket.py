#!/usr/bin/env python3
"""Install Coilmarket's traction substation, tram service, and regional encounters."""
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from reedwake_district_assets import append_district_tiles, install_trainer_art

source, assets = map(Path, sys.argv[1:3])
GYM = "data/maps/LavaridgeTown_Gym_1F"
WIDTH, HEIGHT = 17, 19
GATE_Y, GATE_X = 7, (7, 8, 9)
METER, STATION = (7, 9), (13, 3)
MAIN_LIMIT, AUX_LIMIT, TRAM_LOAD = 7, 5, 4
SOLVED = 5
STATE_VAR = "VAR_COILMARKET_SWITCHES"
# The set bit moves this load away from its default feeder.
LOADS = (
    ("Market", (3, 12), 3, "main"),
    ("Cold", (7, 12), 2, "aux"),
    ("Signal", (11, 12), 2, "aux"),
)


def edit(path, transform):
    file = source / path
    file.write_text(transform(file.read_text(encoding="utf-8")), encoding="utf-8")


def replace(text, before, after):
    if text.count(before) != 1:
        raise SystemExit(f"Expected one match for {before[:80]!r}")
    return text.replace(before, after, 1)


def strings(lines):
    return "".join(
        f'\t.string "{line}"\n' if i == len(lines) - 1 or line.endswith(("\\n", "\\p", "\\l"))
        else f'\t.string "{line}\\n"\n'
        for i, line in enumerate(lines)
    )


def dialogue(text, label, lines):
    pattern = rf"(?m)^{label}:\n(?:\t\.string .+\n)+"
    result, count = re.subn(pattern, lambda _: label + ":\n" + strings(lines), text)
    if count != 1:
        raise SystemExit(f"Expected one text block for {label}")
    return result


def read_json(path):
    return json.loads((source / path).read_text(encoding="utf-8"))


def write_json(path, data):
    (source / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def feeders(state):
    return tuple(
        ("aux" if default == "main" else "main") if state & (1 << index) else default
        for index, (_, _, _, default) in enumerate(LOADS)
    )


def power_reading(state):
    connections = feeders(state)
    main = TRAM_LOAD + sum(load[2] for load, feeder in zip(LOADS, connections) if feeder == "main")
    aux = TRAM_LOAD + sum(load[2] for load in LOADS) - main
    return main, aux, connections[-1]


def power_faults(state):
    main, aux, signal = power_reading(state)
    faults = []
    if main > MAIN_LIMIT:
        faults.append("MAIN is overloaded.")
    if aux > AUX_LIMIT:
        faults.append("AUX is overloaded.")
    if signal != "main":
        faults.append("Signal must share MAIN with the tram.")
    return faults


def tile_art():
    palette = [
        (0, 0, 0), (23, 25, 40), (32, 37, 54), (45, 49, 66),
        (62, 68, 83), (83, 89, 101), (110, 121, 126), (146, 152, 145),
        (211, 217, 201), (98, 60, 63), (150, 88, 68), (188, 124, 67),
        (235, 178, 91), (73, 104, 117), (87, 185, 183), (182, 237, 189),
    ]
    tiles = {}

    def tile(name, fill):
        tiles[name] = Image.new("P", (16, 16), fill)
        return ImageDraw.Draw(tiles[name])

    draw = tile("deck", 4)
    draw.line((0, 0, 15, 0), fill=5)
    draw.line((0, 15, 15, 15), fill=3)
    draw.point([(2, 2), (13, 2), (2, 13), (13, 13)], fill=6)
    draw.line((3, 9, 6, 9), fill=5)

    draw = tile("wall", 2)
    draw.rectangle((0, 1, 15, 13), fill=3, outline=1)
    draw.line((1, 2, 14, 2), fill=6)
    draw.line((0, 12, 15, 12), fill=5)
    draw.rectangle((3, 4, 12, 10), fill=4, outline=2)
    draw.line((4, 7, 11, 7), fill=2)

    draw = tile("rack", 3)
    draw.rectangle((1, 1, 14, 14), fill=2, outline=9)
    for x in (3, 7, 11):
        draw.rectangle((x, 3, x + 1, 12), fill=10)
        draw.point((x, 3), fill=12)
        draw.point((x, 12), fill=11)

    draw = tile("track", 2)
    for y in (3, 8, 13):
        draw.rectangle((1, y, 14, y + 1), fill=9)
    for x in (4, 11):
        draw.line((x, 0, x, 15), fill=7)
        draw.line((x + 1, 0, x + 1, 15), fill=5)

    for name, light in (("main", 12), ("aux", 14)):
        draw = tile("switch_" + name, 4)
        draw.rectangle((1, 2, 14, 14), fill=2, outline=10)
        draw.rectangle((3, 4, 12, 9), fill=1, outline=6)
        draw.line((5, 7, 10, 7), fill=6)
        draw.rectangle((4 if name == "main" else 9, 6,
                        6 if name == "main" else 11, 8), fill=light)
        draw.point([(4, 12), (11, 12)], fill=light)

        draw = tile("wire_" + name, 4)
        draw.rectangle((5, 0, 10, 15), fill=2)
        draw.line((7, 0, 7, 15), fill=light)
        draw.line((8, 0, 8, 15), fill=11 if name == "main" else 13)
        draw.line((4, 5, 11, 5), fill=6)
        draw.line((4, 11, 11, 11), fill=6)

    for name, good in (("on", True), ("off", False)):
        draw = tile("gate_" + name, 3)
        draw.rectangle((0, 0, 15, 15), outline=2)
        if good:
            for x in (4, 11):
                draw.line((x, 0, x, 15), fill=6)
                draw.point((x, 8), fill=15)
            draw.line((1, 11, 14, 11), fill=14)
        else:
            draw.rectangle((1, 3, 14, 12), fill=9, outline=10)
            for x in (2, 7, 12):
                draw.line((x, 4, x + 2, 6), fill=12)
                draw.line((x, 9, x + 2, 11), fill=11)

    for name, light in (("meter", 12), ("station", 15)):
        draw = tile(name, 4)
        draw.rectangle((1, 2, 14, 14), fill=2, outline=10)
        draw.rectangle((3, 4, 12, 10), fill=1, outline=6)
        draw.line((4, 8, 6, 8, 7, 6, 9, 8, 11, 6), fill=light)
        draw.point([(4, 12), (8, 12), (11, 12)], fill=light)
    return palette, tiles


def install_layout(ids):
    path = source / "data/layouts/LavaridgeTown_Gym_1F/map.bin"
    count = WIDTH * HEIGHT
    grid = list(struct.unpack(f"<{count}H", path.read_bytes()))
    exits = {x: grid[(HEIGHT - 1) * WIDTH + x] for x in (13, 14)}

    def put(x, y, name, solid=False):
        grid[y * WIDTH + x] = ids[name] | 0x3000 | (0x400 if solid else 0)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x in (0, WIDTH - 1) or y in (0, 1, HEIGHT - 1, GATE_Y):
                put(x, y, "wall", True)
            elif x == 8 and 4 <= y <= 6:
                put(x, y, "track")
            else:
                put(x, y, "deck")

    for x in GATE_X:
        put(x, GATE_Y, "gate_off", True)
    for (_, (x, y), _, _), feeder in zip(LOADS, feeders(0)):
        if (x, y - 2) != (METER[0], METER[1] + 1):
            put(x, y - 2, "rack", True)
        put(x, y - 1, "wire_" + feeder)
        put(x, y, "switch_" + feeder, True)
    for pos, tile in ((METER, "meter"), (STATION, "station"), ((10, 15), "rack"), ((15, 15), "rack")):
        put(*pos, tile, True)
    for x, code in exits.items():
        grid[(HEIGHT - 1) * WIDTH + x] = code
    path.write_bytes(struct.pack(f"<{count}H", *grid))

    path = f"{GYM}/map.json"
    events = read_json(path)
    positions = {
        "Flannery": (8, 3), "Cole": (2, 13), "Gerald": (5, 15),
        "Axle": (10, 11), "Danielle": (14, 10), "GymGuide": (11, 16),
    }
    events["weather"] = "WEATHER_NONE"
    for npc in events["object_events"]:
        name = npc["script"].rsplit("_", 1)[-1]
        npc["x"], npc["y"] = positions[name]
        npc["movement_type"] = "MOVEMENT_TYPE_FACE_DOWN"
        if npc["trainer_type"] == "TRAINER_TYPE_BURIED":
            npc["trainer_type"] = "TRAINER_TYPE_NORMAL"
    events["warp_events"] = [warp for warp in events["warp_events"]
                             if warp["dest_map"] == "MAP_LAVARIDGE_TOWN"]
    events["bg_events"] = [{
        "type": "sign", "x": x, "y": y, "elevation": 0,
        "player_facing_dir": "BG_EVENT_PLAYER_FACING_NORTH", "script": script,
    } for (x, y), script in (
        *((pos, "Coilmarket_Switch" + label) for label, pos, _, _ in LOADS),
        (METER, "Coilmarket_ReadMeter"), (STATION, "Coilmarket_FieldStation"),
        ((10, 15), "LavaridgeTown_Gym_1F_EventScript_LeftGymStatue"),
        ((15, 15), "LavaridgeTown_Gym_1F_EventScript_RightGymStatue"),
    )]
    write_json(path, events)

    path = "data/maps/LavaridgeTown_Gym_B1F/map.json"
    basement = read_json(path)
    for warp in basement["warp_events"]:
        if warp["dest_map"] == "MAP_LAVARIDGE_TOWN_GYM_1F":
            warp["dest_warp_id"] = "0"
    write_json(path, basement)


def grid_scripts(ids):
    def set_tile(x, y, name, solid):
        return f"\tsetmetatile {x}, {y}, 0x{ids[name]:03X}, {int(solid)}\n"

    def dispatch(label):
        text = "".join(f"\tgoto_if_eq {STATE_VAR}, {state}, {label}{state}\n"
                       for state in range(1, 8))
        return text + f"\tgoto {label}0\n"

    text = "Coilmarket_RefreshGrid:\n" + dispatch("Coilmarket_Apply")
    text += "\nCoilmarket_DisplayMeter:\n" + dispatch("Coilmarket_Meter")
    for state in range(8):
        faults = power_faults(state)
        gate = "gate_off" if faults else "gate_on"
        text += f"\nCoilmarket_Apply{state}:\n"
        for x in GATE_X:
            text += set_tile(x, GATE_Y, gate, bool(faults))
        for (_, (x, y), _, _), feeder in zip(LOADS, feeders(state)):
            text += set_tile(x, y, "switch_" + feeder, True)
            text += set_tile(x, y - 1, "wire_" + feeder, False)
        main, aux, signal = power_reading(state)
        lines = [
            f"MAIN {main}/{MAIN_LIMIT}     AUX {aux}/{AUX_LIMIT}",
            f"SIGNAL: {signal.upper()}\\p",
            *(faults or ["Tram in service. Gate released."]),
        ]
        lines[-1] += "$"
        text += f"\treturn\n\nCoilmarket_Meter{state}:\n"
        text += f"\tmsgbox Coilmarket_Text_Meter{state}, MSGBOX_DEFAULT\n\treturn\n"
        text += f"\nCoilmarket_Text_Meter{state}:\n" + strings(lines)
    for index, (name, _, _, _) in enumerate(LOADS):
        bit = 1 << index
        text += f"\nCoilmarket_Switch{name}::\n\tlockall\n"
        text += "\tgoto_if_set FLAG_BADGE04_GET, Coilmarket_GridLocked\n"
        for state in range(8):
            if state & bit:
                text += f"\tgoto_if_eq {STATE_VAR}, {state}, Coilmarket_Reset{name}\n"
        text += f"\taddvar {STATE_VAR}, {bit}\n\tgoto Coilmarket_GridChanged\n"
        text += f"\nCoilmarket_Reset{name}:\n\tsubvar {STATE_VAR}, {bit}\n\tgoto Coilmarket_GridChanged\n"
    return text


GYM_TEXT = {
    "GymGuideAdvice": [
        r"Left: MARKET (3). Center: COLD (2).",
        r"Right: SIGNAL (2). The tram draws 4.\p",
        r"Each switch moves its load to the",
        r"other feeder. The tram uses MAIN.\p",
        r"Keep its signal on MAIN too. The",
        r"meter shows what each side can take.\p",
        r"BRIN uses ELECTRIC types. Some",
        r"of her partners can leave the ground.$",
    ],
    "GymGuidePostVictory": [r"The tram is running again.",
                             r"I can hear it through the floor.$"],
    "FlanneryIntro": [r"BRIN: Hear that low hum? That's",
                      r"the tram pulling out of the yard.\p",
                      r"ARCRAIL can feel each motor start.",
                      r"Let's see what it makes of you.$"],
    "FlanneryDefeat": [r"BRIN: The grid held, and so did you.",
                        r"The HEAT BADGE is yours.$"],
    "ReceivedHeatBadge": [r"{PLAYER} received the HEAT BADGE",
                           r"from BRIN.$"],
    "ExplainHeatBadgeTakeThis": [r"Use STRENGTH outside of battle with",
                                  r"the HEAT BADGE.\p",
                                  r"Traded POKéMON through Lv. 50 will",
                                  r"listen to you, too. Take this TM.$"],
    "ExplainOverheat": [r"TM34 contains SHOCK WAVE.",
                         r"Even an evasive target can't shake",
                         r"an ELECTRIC field that wide.$"],
    "RegisteredFlannery": [r"Registered GYM LEADER BRIN",
                            r"in the POKéNAV.$"],
    "FlanneryPostBattle": [r"The field station is live now.\p",
                           r"The sand out on ASHSWITCH carries",
                           r"iron filings. Look for ARCRAIL",
                           r"after you get your GO-GOGGLES.$"],
    "GymStatue": [r"COILMARKET GYM\p", r"LEADER: BRIN", r"TRACTION SUBSTATION$"],
    "GymStatueCertified": [r"COILMARKET GYM\p", r"CERTIFIED SURVEYOR: {PLAYER}$"],
    "FlanneryPreRematch": [r"BRIN: I've got two crews on call.",
                            r"Ready for a double battle?$"],
    "FlanneryRematchDefeat": [r"That was a clean run from both of you.$"],
    "FlanneryPostRematch": [r"BRIN: I'll show the crew that one.$"],
    "FlanneryRematchNeedTwoMons": [r"BRIN: Bring two partners so we can",
                                   r"test both sides of the grid.$"],
    "ColeIntro": [r"The market lights just flickered.",
                   r"Stay here until I check the breaker!$"],
    "ColeDefeat": [r"I should have brought a spare.$"],
    "ColePostBattle": [r"The market draws three units.",
                         r"That one's the biggest switchable load.$"],
    "GeraldIntro": [r"Cold storage can't go dark.",
                     r"Give my backup crew a test run.$"],
    "GeraldDefeat": [r"That's a sharp change in load.$"],
    "GeraldPostBattle": [r"Cold storage draws two units.",
                          r"Either feeder can run it.$"],
    "AxleIntro": [r"Nothing moves until the signal clears.",
                   r"My crew has time for a battle.$"],
    "AxleDefeat": [r"Guess your crew has the clearer signal.$"],
    "AxlePostBattle": [r"The signal shares a circuit with",
                        r"the tram when the gate is open.$"],
    "DanielleIntro": [r"I keep a partner who can reach",
                       r"the lines above the yard.$"],
    "DanielleDefeat": [r"Right down to the last spark.$"],
    "DaniellePostBattle": [r"The tram always draws four.",
                            r"Leave room on MAIN for its signal.$"],
}


def install_gym_scripts(ids):
    helper = Path(__file__).with_name("coilmarket_grid.inc").read_text(encoding="utf-8")

    def apply(text):
        a = text.index("LavaridgeTown_Gym_1F_OnTransition:\n")
        b = text.index("LavaridgeTown_Gym_1F_EventScript_Flannery::\n", a)
        text = text[:a] + (
            "LavaridgeTown_Gym_1F_OnTransition:\n"
            "\tcall_if_set FLAG_BADGE04_GET, Coilmarket_ParkGrid\n"
            "\tcall Coilmarket_RefreshGrid\n\tend\n\n"
        ) + text[b:]
        text = replace(text, "LavaridgeTown_Gym_1F_EventScript_Flannery::\n",
                       "LavaridgeTown_Gym_1F_EventScript_Flannery::\n"
                       f"\tgoto_if_ne {STATE_VAR}, {SOLVED}, Coilmarket_ReturnToEntrance\n")
        text = replace(text, "LavaridgeTown_Gym_EventScript_CheckTrainerScript::\n"
                       "\tcall LavaridgeTown_Gym_1F_EventScript_SetTrainerTempVars\n",
                       "LavaridgeTown_Gym_EventScript_CheckTrainerScript::\n")
        text = text.replace("giveitem ITEM_TM_OVERHEAT", "giveitem ITEM_TM_SHOCK_WAVE")
        for label, lines in GYM_TEXT.items():
            text = dialogue(text, "LavaridgeTown_Gym_1F_Text_" + label, lines)
        return text + "\n" + helper + "\n" + grid_scripts(ids)

    edit(f"{GYM}/scripts.inc", apply)


def install_teams():
    lineups = {
        "Cole": [("ELECTRIKE", 28, ())],
        "Axle": [("MANECTRIC", 28, ())],
        "Gerald": [
            ("ELECTRIKE", 27, ("SPARK", "QUICK_ATTACK", "THUNDER_WAVE", "NONE")),
            ("MANECTRIC", 29, ("SHOCK_WAVE", "BITE", "QUICK_ATTACK", "NONE")),
        ],
        "Danielle": [("DELTA_VANEAGLE", 29, ("SPARK", "WING_ATTACK", "QUICK_ATTACK", "NONE"))],
        "Flannery1": [
            ("MANECTRIC", 31, ("SHOCK_WAVE", "BITE", "THUNDER_WAVE", "QUICK_ATTACK")),
            ("DELTA_VANEAGLE", 31, ("SHOCK_WAVE", "AERIAL_ACE", "QUICK_ATTACK", "AGILITY")),
            ("PLUSLE", 33, ("SHOCK_WAVE", "METAL_CLAW", "SANDSTORM", "ROCK_TOMB")),
        ],
        "Flannery2": [
            ("MANECTRIC", 39, ("SPARK", "BITE", "THUNDER_WAVE", "QUICK_ATTACK")),
            ("DELTA_VANEAGLE", 39, ("SHOCK_WAVE", "AERIAL_ACE", "QUICK_ATTACK", "AGILITY")),
            ("PLUSLE", 41, ("THUNDERBOLT", "METAL_CLAW", "SANDSTORM", "ROCK_TOMB")),
        ],
        "Flannery3": [
            ("DELTA_VOLTRACK", 43, ("THUNDERBOLT", "SHADOW_BALL", "TACKLE", "THUNDER_WAVE")),
            ("DELTA_VANEAGLE", 44, ("THUNDERBOLT", "AERIAL_ACE", "QUICK_ATTACK", "AGILITY")),
            ("PLUSLE", 46, ("THUNDERBOLT", "IRON_TAIL", "SANDSTORM", "ROCK_TOMB")),
        ],
        "Flannery4": [
            ("DELTA_VOLTRACK", 48, ("THUNDERBOLT", "SHADOW_BALL", "PROTECT", "THUNDER_WAVE")),
            ("DELTA_VANEAGLE", 49, ("THUNDERBOLT", "AERIAL_ACE", "QUICK_ATTACK", "AGILITY")),
            ("DELTA_ARCRAIL", 51, ("THUNDERBOLT", "IRON_TAIL", "SHADOW_BALL", "ROCK_TOMB")),
        ],
        "Flannery5": [
            ("DELTA_VOLTRACK", 53, ("THUNDERBOLT", "SHADOW_BALL", "PROTECT", "THUNDER_WAVE")),
            ("DELTA_VANEAGLE", 54, ("THUNDERBOLT", "AERIAL_ACE", "QUICK_ATTACK", "AGILITY")),
            ("DELTA_ARCRAIL", 56, ("THUNDERBOLT", "IRON_TAIL", "SHADOW_BALL", "ROCK_TOMB")),
        ],
    }

    def trainers(text):
        pattern = r"(?ms)^    \[TRAINER_FLANNERY_[1-5]\] =\n    \{.*?^    \},"
        text, count = re.subn(pattern, lambda m: replace(m[0], '_("FLANNERY")', '_("BRIN")'), text)
        if count != 5:
            raise SystemExit(f"Expected five Brin trainer records, found {count}")
        return text

    def parties(text):
        for trainer, party in lineups.items():
            pattern = rf"(?ms)^static const struct (TrainerMon\w+) sParty_{trainer}\[\] = \{{.*?^\}};"
            match = re.search(pattern, text)
            if match is None:
                raise SystemExit(f"Missing party for {trainer}")
            kind = match[1]
            members = []
            for species, level, moves in party:
                fields = [f".iv = 130, .lvl = {level}, .species = SPECIES_{species}"]
                if kind.startswith("TrainerMonItem"):
                    item = "SITRUS_BERRY" if species in ("PLUSLE", "DELTA_ARCRAIL") else "NONE"
                    fields.append(".heldItem = ITEM_" + item)
                if kind.endswith("CustomMoves"):
                    fields.append(".moves = {" + ", ".join("MOVE_" + move for move in moves) + "}")
                members.append("    {" + ", ".join(fields) + "},")
            text = replace(text, match[0], f"static const struct {kind} sParty_{trainer}[] = {{\n"
                           + "\n".join(members) + "\n};")
        return text

    edit("src/data/trainers.h", trainers)
    edit("src/data/trainer_parties.h", parties)
    install_trainer_art(assets / "brin.png", source / "graphics/trainers/front_pics/leader_flannery.png")


def install_trams():
    for town, old, label, target, arrival, destination, outbound in (
        ("MauvilleCity", "RichBoy", "TramToCoilmarket", "MAP_LAVARIDGE_TOWN", (6, 8), "COILMARKET", True),
        ("LavaridgeTown", "OldMan", "TramToKitewatch", "MAP_MAUVILLE_CITY", (25, 10), "KITEWATCH", False),
    ):
        path = f"data/maps/{town}/map.json"
        events = read_json(path)
        operator = next(npc for npc in events["object_events"]
                        if npc["script"] == f"{town}_EventScript_{old}")
        operator.update(graphics_id="OBJ_EVENT_GFX_SAILOR", movement_type="MOVEMENT_TYPE_FACE_RIGHT",
                        movement_range_x=0, movement_range_y=0, script="Coilmarket_" + label)
        write_json(path, events)

        start = f"\nCoilmarket_{label}::\n\tlock\n\tfaceplayer\n"
        if outbound:
            start += "\tgoto_if_unset FLAG_BADGE03_GET, Coilmarket_TramHold\n"
        start += (
            f"\tmsgbox Coilmarket_Text_{label}, MSGBOX_YESNO\n"
            f"\tgoto_if_eq VAR_RESULT, NO, Coilmarket_{label}End\n"
            f"\twarp {target}, {arrival[0]}, {arrival[1]}\n\twaitstate\n"
            f"Coilmarket_{label}End:\n\trelease\n\tend\n\n"
            f"Coilmarket_Text_{label}:\n"
            + strings([r"The survey tram is boarding.\p", f"Ride to {destination}?$"])
        )
        if outbound:
            start += (
                "\nCoilmarket_TramHold:\n\tmsgbox Coilmarket_Text_TramHold, MSGBOX_DEFAULT\n"
                "\trelease\n\tend\n\nCoilmarket_Text_TramHold:\n"
                + strings(["The hill line takes certified surveyors.",
                           "Get your badge from VENN first.$"])
            )
        edit(f"data/maps/{town}/scripts.inc", lambda text: text + start)

    edit("data/maps/MauvilleCity_Gym/scripts.inc", lambda text:
        dialogue(text, "MauvilleCity_Gym_Text_WattsonPostBattle", [
            r"The field station is open now.\p",
            "Take the survey tram to COILMARKET.",
            "The operator waits by the south road,",
            "just past the POKéMON CENTER.$",
        ]))
    edit("data/maps/LavaridgeTown/scripts.inc", lambda text:
        dialogue(dialogue(text, "LavaridgeTown_Text_TownSign", [
            r"COILMARKET\p", "Hot springs beneath the tram yard.$",
        ]), "LavaridgeTown_Text_GymSign", [
            r"COILMARKET GYM\p", "LEADER: BRIN", "TRACTION SUBSTATION$",
        ]))


def install_encounters():
    path = "src/data/region_map/region_map_sections.json"
    region = read_json(path)
    fields = {
        "MAPSEC_LAVARIDGE_TOWN": "COILMARKET", "MAPSEC_ROUTE_111": "ASHSWITCH",
        "MAPSEC_ROUTE_112": "WIREGRASS WAY", "MAPSEC_ROUTE_113": "CINDER SPUR",
    }
    for area in region["map_sections"]:
        if area["id"] in fields:
            area["name"] = fields[area["id"]]
    write_json(path, region)

    path = "src/data/wild_encounters.json"
    encounters = read_json(path)
    replacements = {
        "MAP_ROUTE111": {9: ("ELECTRIKE", 23), 10: ("MANECTRIC", 25), 11: ("PLUSLE", 30)},
        "MAP_ROUTE112": {0: ("ELECTRIKE", 16), 3: ("ELECTRIKE", 17), 8: ("ELECTRIKE", 18),
                         11: ("MANECTRIC", 21)},
        "MAP_ROUTE113": {1: ("ELECTRIKE", 18), 4: ("ELECTRIKE", 19), 8: ("MANECTRIC", 22),
                         11: ("MANECTRIC", 25)},
    }
    seen = set()
    for group in encounters["wild_encounter_groups"]:
        for area in group["encounters"]:
            key = area.get("map")
            if key in replacements:
                slots = area["land_mons"]["mons"]
                for index, (species, level) in replacements[key].items():
                    slots[index].update(species="SPECIES_" + species, min_level=level, max_level=level)
                seen.add(key)
    if seen != replacements.keys():
        raise SystemExit("Missing Coilmarket encounter map")
    write_json(path, encounters)


edit("include/constants/vars.h", lambda text:
    replace(text, "VAR_UNUSED_0x40FF                                0x40FF // Unused Var",
                  "VAR_COILMARKET_SWITCHES                          0x40FF"))
if [state for state in range(8) if not power_faults(state)] != [SOLVED]:
    raise SystemExit("Expected one valid traction grid configuration")
palette, tiles = tile_art()
tile_ids = append_district_tiles(source / "data/tilesets/secondary/lavaridge_gym", palette, tiles)
install_layout(tile_ids)
install_gym_scripts(tile_ids)
install_teams()
install_trams()
install_encounters()
