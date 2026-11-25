#!/usr/bin/env python3
"""Wire the optional timeline into the stock single-battle controllers."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TOOLS = Path(__file__).parent
HEADER = """
u8 ReedwakeQueueLimit(void);
bool8 ReedwakeCanQueue(u16 move);
u8 ReedwakeTimelineTarget(u8 battler, u16 move);
u8 ReedwakeMoveSpeed(u16 move);
void ReedwakeCancelQueue(void);
void ReedwakeSetTextboxTint(bool8 tinted);
bool8 ReedwakeSetQueue(u8 battler, const u8 *slots, const u8 *positions, u8 count);
s32 ReedwakeTimelineDamage(s32 damage);
bool8 ReedwakeGuardRecoil(void);
bool8 ReedwakeReleaseCharge(void);
void ReedwakePositionHit(void);
"""


def replace(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f"Could not uniquely locate {old[:100]!r}")
    return text.replace(old, new, 1)


def edit(path, changes):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    for old, new in changes:
        text = replace(text, old, new)
    file.write_text(text, encoding="utf-8")


(ROOT / "include/reedwake_timeline.h").write_text(
    "#ifndef GUARD_REEDWAKE_TIMELINE_H\n#define GUARD_REEDWAKE_TIMELINE_H\n"
    + HEADER + "\n#endif\n", encoding="utf-8")
header = '#include "global.h"\n'
with_header = header + '#include "reedwake_timeline.h"\n'
start = "static void CB2_InitBattleInternal(void)\n{\n    s32 i;\n"
focus = "static void CheckFocusPunch_ClearVarsBeforeTurnStarts(void)\n{"
run = "static void RunTurnActionsFunctions(void)\n{\n"
timeline = (TOOLS / "reedwake_timeline.inc").read_text(encoding="utf-8")
edit("src/battle_main.c", [
    (header, with_header),
    ("static void CB2_InitBattleInternal(void);", "static void ReedwakeReset(void);\nstatic void CB2_InitBattleInternal(void);"),
    (start, start + "\n    ReedwakeReset();\n"),
    (focus, timeline + "\n" + focus),
    ("    gBattleMainFunc = RunTurnActionsFunctions;\n    gBattleCommunication[3] = 0;",
     "    ReedwakeStart();\n    gBattleMainFunc = RunTurnActionsFunctions;\n    gBattleCommunication[3] = 0;"),
    (run, run + """    if (ReedwakeAnimateReaction())
        return;
    if (sTimeline.active && sTimeline.started && gCurrentActionFuncId == B_ACTION_USE_MOVE
        && IsTextPrinterActive(B_WIN_MSG))
        return;
    if (sTimeline.active && !sTimeline.started)
    {
        if (ReedwakeAdvance())
            return;
        ReedwakeReset();
        gCurrentTurnActionNumber = gBattlersCount;
        gHitMarker &= ~HITMARKER_PASSIVE_HP_UPDATE;
        gBattleMainFunc = sEndTurnFuncsTable[gBattleOutcome & 0x7F];
        return;
    }
"""),
    ("    sTurnActionsFuncsTable[gCurrentActionFuncId]();\n\n    if (gCurrentTurnActionNumber",
     """    sTurnActionsFuncsTable[gCurrentActionFuncId]();

    if (sTimeline.active && gCurrentTurnActionNumber != 0)
    {
        sTimeline.started = FALSE;
        gHitMarker &= ~(HITMARKER_NO_ATTACKSTRING | HITMARKER_UNABLE_TO_USE_MOVE);
        return;
    }

    if (gCurrentTurnActionNumber"""),
])
choose_def = "static void HandleInputChooseMove(void)\n{"
menu = (TOOLS / "reedwake_timeline_menu.inc").read_text(encoding="utf-8")
edit("src/battle_controller_player.c", [
    (header, with_header),
    (choose_def, menu + "\n" + choose_def),
    ("    bool32 canSelectTarget = FALSE;\n    struct ChooseMoveStruct *moveInfo = (struct ChooseMoveStruct *)(&gBattleBufferA[gActiveBattler][4]);\n\n",
     "    bool32 canSelectTarget = FALSE;\n    struct ChooseMoveStruct *moveInfo = (struct ChooseMoveStruct *)(&gBattleBufferA[gActiveBattler][4]);\n\n"
     "    if (ReedwakeMoveInput(moveInfo))\n        return;\n\n"),
    ("        u8 moveTarget;\n\n        PlaySE(SE_SELECT);",
     "        u8 moveTarget;\n\n        ReedwakeSetTextboxTint(FALSE);\n        PlaySE(SE_SELECT);"),
    ("static void PlayerHandleChooseMove(void)\n{\n",
     "static void PlayerHandleChooseMove(void)\n{\n    ReedwakeCancelQueue();\n    sReedwakeCount = 0;\n    sReedwakeAim = 0;\n"),
    ("    txtPtr = StringCopy(gDisplayedStringBattle, gText_MoveInterfaceType);",
     "    if (sReedwakeCount || sReedwakeAim)\n    {\n        ReedwakeShowQueue();\n        return;\n    }\n"
     "    txtPtr = StringCopy(gDisplayedStringBattle, gText_MoveInterfaceType);"),
])
edit("src/battle_util.c", [
    (header, with_header),
    ("        gBattlescriptCurrInstr = gBattleScriptsForMoveEffects[gBattleMoves[gCurrentMove].effect];\n    }\n\n    if (gBattleTypeFlags & BATTLE_TYPE_ARENA)",
     "        if ((gCurrentMove == MOVE_DIG || gCurrentMove == MOVE_FLY) && ReedwakeReleaseCharge())\n"
     "            gBattlescriptCurrInstr = gBattleScriptsForMoveEffects[EFFECT_HIT];\n"
     "        else\n            gBattlescriptCurrInstr = gBattleScriptsForMoveEffects[gBattleMoves[gCurrentMove].effect];\n"
     "    }\n\n    if (gBattleTypeFlags & BATTLE_TYPE_ARENA)"),
    ("void HandleAction_ActionFinished(void)\n{\n", "void HandleAction_ActionFinished(void)\n{\n    ReedwakePositionHit();\n"),
])
edit("src/battle_script_commands.c", [
    (header, with_header),
    ("static void Cmd_moveend(void)\n{\n", """static EWRAM_DATA s32 sReedwakeRecoilDamage = 0;
static EWRAM_DATA s32 sReedwakeRecoilHpDealt = 0;
static EWRAM_DATA bool8 sReedwakeRecoilReturning = FALSE;

static void Cmd_moveend(void)
{
"""),
    ("    u16 originallyUsedMove;\n\n    if (gChosenMove == MOVE_UNAVAILABLE)",
     """    u16 originallyUsedMove;

    if (sReedwakeRecoilReturning)
    {
        sReedwakeRecoilReturning = FALSE;
        gBattleMoveDamage = sReedwakeRecoilDamage;
        gHpDealt = sReedwakeRecoilHpDealt;
        gHitMarker &= ~HITMARKER_PASSIVE_HP_UPDATE;
    }
    else if (ReedwakeGuardRecoil() && !(gMoveResultFlags & MOVE_RESULT_NO_EFFECT)
        && gHpDealt > 0 && gBattleMons[gBattlerAttacker].hp)
    {
        sReedwakeRecoilReturning = TRUE;
        sReedwakeRecoilDamage = gBattleMoveDamage;
        sReedwakeRecoilHpDealt = gHpDealt;
        gBattleMoveDamage = max(1, gHpDealt / 4);
        BattleScriptPushCursor();
        gBattlescriptCurrInstr = BattleScript_MoveEffectRecoil;
        return;
    }

    if (gChosenMove == MOVE_UNAVAILABLE)"""),
    ("    if (gProtectStructs[gBattlerAttacker].helpingHand)\n        gBattleMoveDamage = gBattleMoveDamage * 15 / 10;\n",
     "    if (gProtectStructs[gBattlerAttacker].helpingHand)\n        gBattleMoveDamage = gBattleMoveDamage * 15 / 10;\n"
     "    gBattleMoveDamage = ReedwakeTimelineDamage(gBattleMoveDamage);\n"),
])

edit("src/pokemon_summary_screen.c", [
    (header, with_header),
    ("static const u8 sTextColors[][3] =", '''static const u8 sReedwakeMoveSpeed[] = _("Speed");
static const u8 sTextColors[][3] ='''),
    ("    PrintTextOnWindow(PSS_LABEL_WINDOW_MOVES_POWER_ACC, gText_Power, 0, 1, 0, 1);\n"
     "    PrintTextOnWindow(PSS_LABEL_WINDOW_MOVES_POWER_ACC, gText_Accuracy2, 0, 17, 0, 1);",
     '''    AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL, 0, 0, 0, 0, sTextColors[1], 0, gText_Power);
    AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL, 0, 10, 0, 0, sTextColors[1], 0, gText_Accuracy2);
    AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL, 0, 20, 0, 0, sTextColors[1], 0, sReedwakeMoveSpeed);'''),
    ("FillWindowPixelRect(PSS_LABEL_WINDOW_MOVES_POWER_ACC, PIXEL_FILL(0), 53, 0, 19, 32);",
     "FillWindowPixelRect(PSS_LABEL_WINDOW_MOVES_POWER_ACC, PIXEL_FILL(0), 42, 0, 30, 32);"),
    ("        PrintTextOnWindow(PSS_LABEL_WINDOW_MOVES_POWER_ACC, text, 53, 1, 0, 0);",
     "        AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL, GetStringRightAlignXOffset(FONT_SMALL, text, 71), 0, 0, 0, sTextColors[0], 0, text);"),
    ("        PrintTextOnWindow(PSS_LABEL_WINDOW_MOVES_POWER_ACC, text, 53, 17, 0, 0);",
     '''        AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL, GetStringRightAlignXOffset(FONT_SMALL, text, 71), 10, 0, 0, sTextColors[0], 0, text);
        if (ReedwakeMoveSpeed(moveIndex) > 100)
            text = gText_ThreeDashes;
        else
        {
            ConvertIntToDecimalStringN(gStringVar1, ReedwakeMoveSpeed(moveIndex), STR_CONV_MODE_RIGHT_ALIGN, 3);
            text = gStringVar1;
        }
        AddTextPrinterParameterized4(PSS_LABEL_WINDOW_MOVES_POWER_ACC, FONT_SMALL,
            GetStringRightAlignXOffset(FONT_SMALL, text, 71), 20, 0, 0, sTextColors[0], 0, text);'''),
])
