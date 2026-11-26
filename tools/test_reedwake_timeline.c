/* Host harness for the scheduler. The ROM supplies these fields and callbacks. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;
typedef int16_t s16;

#define EWRAM_DATA
#define _(text) text
#define TRUE 1
#define RGB(r, g, b) ((r) | ((g) << 5) | ((b) << 10))
#define MAX_SPRITES 64
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
#define PIXEL_FILL(c) ((c) * 17)
#define FONT_SMALL 0
#define COPYWIN_FULL 0
#define SE_SELECT 0
#define FALSE 0
#define max(a, b) ((a) > (b) ? (a) : (b))
#define JOY_NEW(mask) (keys & (mask))
enum { DPAD_UP = 1, DPAD_DOWN = 2, DPAD_RIGHT = 4, DPAD_ANY = 7,
       A_BUTTON = 8, B_BUTTON = 16, R_BUTTON = 32, DPAD_LEFT = 64 };
#include "constants/moves.h"
#include "constants/battle_move_effects.h"
enum { MOVE_TARGET_USER = 16, MOVE_TARGET_USER_OR_SELECTED = 2 };
enum { FLAG_BADGE01_GET = 0, FLAG_BADGE08_GET = 7, STAT_SPEED = 0, STATUS1_PARALYSIS = 1,
       TYPE_GROUND = 1, TYPE_DARK, TYPE_FLYING, TYPE_GHOST, STATUS2_MULTIPLETURNS = 2, STATUS2_RECHARGE = 4,
       B_ACTION_USE_MOVE = 0, B_ACTION_FINISHED = 1, B_WIN_MSG = 0, MOVE_RESULT_NO_EFFECT = 1,
       BATTLE_TYPE_DOUBLE = 1, BATTLE_TYPE_LINK = 2, BATTLE_TYPE_RECORDED = 4, BATTLE_TYPE_FRONTIER = 8,
       BATTLE_TYPE_SAFARI = 16, BATTLE_TYPE_WALLY_TUTORIAL = 32, BATTLE_TYPE_TRAINER = 64 };
static u8 keys, badges = 3, gBattlersCount = 2, gChosenActionByBattler[2];
static u32 gBattleTypeFlags, gBattleControllerExecFlags;
static u8 gBattlerPartyIndexes[2], gBattlerByTurnOrder[2], gActionsByTurnOrder[2];
static u8 gCurrentTurnActionNumber, gCurrentActionFuncId, gBattlerAttacker, gBattlerTarget;
static u8 gBattleOutcome, gMoveResultFlags, lastMessage[128];
static u16 gBattle_BG0_X, gBattle_BG0_Y, gCurrentMove, gChosenMoveByBattler[2];
static const u8 gStatStageRatios[][2] = {{1, 1}};
static const u8 gMoveNames[MOVES_COUNT][16] = {[MOVE_EARTHQUAKE] = "Earthquake", [MOVE_POUND] = "Pound", [MOVE_TACKLE] = "Tackle"};
static struct { int8_t priority; u8 power, accuracy, target, effect; } gBattleMoves[MOVES_COUNT];
static struct { u16 speed, attack, defense, hp, moves[4]; u8 pp[4], statStages[1], types[2], nickname[11];
                u32 status1, status2; } gBattleMons[2];
static struct { u16 encoredMove; } gDisableStructs[2];
static struct { u8 noValidMoves; } gProtectStructs[2];
static struct { u8 chosenMovePositions[2], moveTarget[2]; } battleStruct, *gBattleStruct = &battleStruct;
struct Sprite { bool8 inUse; s16 x2, y2; };
static struct Sprite gSprites[MAX_SPRITES];
static u8 gBattlerSpriteIds[2] = {0,1};
static u16 gPlttBufferUnfaded[16];
static void LoadPalette(const void *src, u16 start, u16 size)
{
    memcpy(&gPlttBufferUnfaded[start], src, size);
}
static void FillWindowPixelBuffer(u8 window, u8 fill) {}
static void FillWindowPixelRect(u8 window, u8 fill, u8 x, u8 y, u8 width, u8 height) {}
static void AddTextPrinterParameterized4(u8 window, u8 font, u8 x, u8 y, u8 letter,
                                        u8 line, const u8 *colors, u8 speed, const u8 *text) {}
static void PutWindowTilemap(u8 window) {}
static void CopyWindowToVram(u8 window, u8 mode) {}
static void PlaySE(u16 sound) {}
static u16 roll = 1;
static u16 Random(void) { return roll; }
static bool8 FlagGet(u16 flag) { return flag < badges; }
static bool8 IsTextPrinterActive(u8 window) { return FALSE; }
static void BattlePutTextOnWindow(const u8 *message, u8 window)
{
    assert(message[0]);
    strcpy((char *)lastMessage, (const char *)message);
}
static u8 *StringCopy(u8 *dest, const u8 *source)
{
    size_t length = strlen((const char *)source);
    memcpy(dest, source, length + 1);
    return dest + length;
}

static u8 *StringCopy_Nickname(u8 *dest, const u8 *source) { return StringCopy(dest, source); }

#include "reedwake_timeline.inc"

static void Setup(u16 playerMove, u16 opponentMove)
{
    ReedwakeReset();
    memset(gBattleMons, 0, sizeof(gBattleMons));
    gBattleMons[0].speed = 95;
    gBattleMons[1].speed = 80;
    gBattleMons[0].attack = gBattleMons[0].defense = 100;
    gBattleMons[1].attack = gBattleMons[1].defense = 100;
    gBattleMons[0].hp = gBattleMons[1].hp = 100;
    gBattleMons[0].moves[0] = playerMove;
    gBattleMons[0].moves[1] = MOVE_TACKLE;
    gBattleMons[1].moves[0] = opponentMove;
    gBattleMons[0].pp[0] = gBattleMons[0].pp[1] = gBattleMons[1].pp[0] = 10;
    gBattleMoves[playerMove].power = gBattleMoves[opponentMove].power = 40;
    gBattleMoves[playerMove].accuracy = gBattleMoves[opponentMove].accuracy = 100;
    gChosenMoveByBattler[1] = opponentMove;
    keys = 0;
    roll = 1;
}

static void FinishSlide(void)
{
    keys = 0;
    assert(sTimeline.menuVisible);
    while (sTimeline.menuFrame < ARRAY_COUNT(sReactionSlide) - 1)
        assert(ReedwakeAdvance() && sTimeline.prompt);
    assert(gBattle_BG0_Y == 0);
}

int main(void)
{
    const u8 slots[] = {0, 0, 0, 0};
    const u8 followUp[] = {0, 1};
    const u8 aim[] = {RW_FRONT, RW_FRONT, RW_FRONT, RW_FRONT};
    u8 i;

    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeQueueLimit() == 3);
    assert(!ReedwakeSetQueue(0, slots, aim, 4));
    ReedwakeStart();
    assert(!ReedwakeAdvance());
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0 && sTimeline.next[0] == 1);
    sTimeline.started = FALSE;
    assert(ReedwakeAdvance() && sTimeline.prompt && sTimeline.incoming == 1);
    FinishSlide();
    keys = B_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.next[1] == 1 && sTimeline.next[0] == 1);
    assert(sTimeline.count[1] == 3);
    for (i = 2; i <= 3; i++)
    {
        keys = 0;
        assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0 && sTimeline.next[0] == i);
        sTimeline.started = FALSE;
        assert(ReedwakeAdvance() && sTimeline.prompt);
        FinishSlide();
        keys = B_BUTTON;
        assert(ReedwakeAdvance() && sTimeline.next[1] == i && sTimeline.next[0] == i);
    }
    assert(!ReedwakeAdvance());

    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    gBattleMons[0].attack = 200;
    roll = 0;
    ReedwakeReact(1, RW_ATTACK, RW_FRONT);
    assert(sTimeline.next[1] == sTimeline.count[1] && sTimeline.next[0] == 1);
    assert(ReedwakeTimelineDamage(100) == 150);

    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 2));
    ReedwakeStart();
    gBattleMons[0].defense = 200;
    ReedwakeReact(1, RW_DEFEND, RW_FRONT);
    assert(ReedwakeTimelineDamage(100) == 35);
    assert(ReedwakeGuardRecoil() && !ReedwakeGuardRecoil());

    Setup(MOVE_TACKLE, MOVE_EARTHQUAKE);
    assert(ReedwakeSetQueue(0, slots, aim, 2));
    ReedwakeStart();
    gBattleMons[0].types[0] = TYPE_FLYING;
    ReedwakeReact(1, RW_DODGE, RW_AIR);
    assert(sTimeline.position[0] == RW_AIR && sTimeline.boost[0]);

    Setup(MOVE_DIG, MOVE_POUND);
    assert(ReedwakeSetQueue(0, followUp, aim, 2));
    ReedwakeStart();
    assert(sTimeline.count[0] == 2);
    ReedwakeAction(0, 100);
    assert(sTimeline.position[0] == RW_UNDER);
    ReedwakeAction(0, 100);
    gBattlerAttacker = 0;
    gBattlerTarget = 1;
    gCurrentMove = MOVE_TACKLE;
    ReedwakePositionHit();
    assert(sTimeline.position[0] == RW_FRONT && sTimeline.position[1] == RW_AIR);

    Setup(MOVE_DIG, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 1));
    ReedwakeStart();
    assert(sTimeline.count[0] == 2 && sTimeline.queue[0][1] == 0);
    Setup(MOVE_TACKLE, MOVE_POUND);
    gBattleMons[1].pp[0] = 1;
    gBattleMons[1].moves[1] = MOVE_TACKLE;
    gBattleMons[1].pp[1] = 2;
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    assert(sTimeline.count[1] == 3);
    assert(sTimeline.queue[1][0] == 0 && sTimeline.queue[1][1] == 1 && sTimeline.queue[1][2] == 1);

    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    gBattleMons[0].defense = 60;
    ReedwakeReact(1, RW_DEFEND, RW_FRONT);
    assert(sTimeline.next[0] == 0 && sTimeline.next[1] == 1);
    assert(ReedwakeTimelineDamage(100) == 125);

    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    gBattleMons[0].speed = 60;
    gBattleMons[1].speed = 90;
    assert(ReedwakeAdvance() && sTimeline.prompt);
    FinishSlide();
    keys = R_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.next[0] == 0 && sTimeline.next[1] == 1);
    assert(ReedwakeTimelineDamage(100) == 125);
    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    gBattleMons[0].speed = 59;
    gBattleMons[1].speed = 90;
    assert(ReedwakeAdvance() && !sTimeline.prompt && sTimeline.started);
    assert(ReedwakeTimelineDamage(100) == 100);
    gBattleMoves[MOVE_SURF].power = 95;
    gBattleMoves[MOVE_QUICK_ATTACK].priority = 1;
    assert(ReedwakeMoveSpeed(MOVE_QUICK_ATTACK) == 0);
    assert(ReedwakeMoveSpeed(MOVE_TACKLE) == 25);
    assert(ReedwakeMoveSpeed(MOVE_POUND) == 25);
    assert(ReedwakeMoveSpeed(MOVE_METAL_CLAW) == 50);
    assert(ReedwakeMoveSpeed(MOVE_SURF) == 100);
    assert(ReedwakeMoveSpeed(MOVE_NONE) > 100);

    /* Three fast player actions fit before the heavy move. Its response is final. */
    Setup(MOVE_TACKLE, MOVE_SURF);
    gBattleMoves[MOVE_SURF].power = 95;
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    for (i = 1; i <= 3; i++)
    {
        assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0);
        assert(sTimeline.next[0] == i && sTimeline.now == 25 * i);
        sTimeline.started = FALSE;
    }
    assert(ReedwakeAdvance() && sTimeline.prompt && sTimeline.now == 100);
    FinishSlide();
    keys = B_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.next[1] == 1);
    assert(!ReedwakeAdvance());

    /* The same cap applies to the player when the opponent finishes first. */
    Setup(MOVE_SURF, MOVE_POUND);
    gBattleMoves[MOVE_SURF].power = 95;
    gBattleMons[0].speed = 50;
    gBattleMons[1].speed = 100;
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    for (i = 1; i <= 3; i++)
    {
        assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 1);
        assert(sTimeline.next[1] == i && sTimeline.now == 25 * i);
        sTimeline.started = FALSE;
    }
    assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0);
    assert(sTimeline.next[0] == 1 && sTimeline.now == 100);
    sTimeline.started = FALSE;
    assert(!ReedwakeAdvance());

    /* Zero-delay moves and the full 0–800 clock fit the scheduler. */
    Setup(MOVE_QUICK_ATTACK, MOVE_SURF);
    gBattleMoves[MOVE_SURF].power = 95;
    assert(ReedwakeSetQueue(0, slots, aim, 2));
    ReedwakeStart();
    sTimeline.clock[0] = sTimeline.clock[1] = 400;
    assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0 && sTimeline.now == 400);
    sTimeline.started = FALSE;
    assert(ReedwakeAdvance() && gBattlerByTurnOrder[0] == 0 && sTimeline.now == 400);
    sTimeline.started = FALSE;
    assert(ReedwakeAdvance() && sTimeline.prompt && sTimeline.now == 500);
    {
        u16 move;
        for (move = MOVE_NONE + 1; move < MOVES_COUNT; move++)
        {
            assert(ReedwakeCanQueue(move));
            assert(ReedwakeMoveSpeed(move) <= 100);
        }
        assert(!ReedwakeCanQueue(MOVE_UNAVAILABLE));
    }
    Setup(MOVE_RECOVER, MOVE_POUND);
    gBattleMoves[MOVE_RECOVER].power = 0;
    gBattleMoves[MOVE_RECOVER].target = MOVE_TARGET_USER;
    assert(ReedwakeSetQueue(0, slots, aim, 3));
    ReedwakeStart();
    sTimeline.boost[0] = TRUE;
    ReedwakeAction(0, 100);
    assert(gBattleStruct->moveTarget[0] == 0 && sTimeline.boost[0]);
    assert(ReedwakeTimelineTarget(0, MOVE_CURSE) == 0);
    gBattleMons[0].types[0] = TYPE_GHOST;
    assert(ReedwakeTimelineTarget(0, MOVE_CURSE) == 1);
    gBattleMons[0].status2 = STATUS2_RECHARGE;
    sTimeline.started = FALSE;
    assert(ReedwakeAdvance() && sTimeline.closingAction && sTimeline.prompt);
    FinishSlide();
    keys = B_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.next[0] == 3 && sTimeline.next[1] == 1);
    assert(!ReedwakeAdvance());

    gBattleMoves[MOVE_SOLAR_BEAM].effect = EFFECT_SOLAR_BEAM;
    gBattleMoves[MOVE_COUNTER].priority = -5;
    assert(ReedwakeMoveSpeed(MOVE_SOLAR_BEAM) == 100);
    assert(ReedwakeMoveSpeed(MOVE_COUNTER) == 100);
    Setup(MOVE_TACKLE, MOVE_POUND);
    strcpy((char *)gBattleMons[0].nickname, "Aipom");
    strcpy((char *)gBattleMons[1].nickname, "Sentret");
    gPlttBufferUnfaded[15] = 0x7FFF;
    assert(ReedwakeSetQueue(0, slots, aim, 2));
    ReedwakeStart();
    assert(gPlttBufferUnfaded[15] == sReedwakeGrey);
    gSprites[1].inUse = TRUE;
    gSprites[1].x2 = 3;
    gSprites[1].y2 = -2;
    ReedwakeReact(0, RW_DEFEND, RW_FRONT);
    assert(strstr((const char *)lastMessage, "Foe Sentret guarded!"));
    assert(strstr((const char *)lastMessage, "\nYour Tackle was blocked!"));
    assert(ReedwakeAnimateReaction() && gSprites[1].x2 != 3);
    for (i = 1; i < 16; i++)
        assert(ReedwakeAnimateReaction());
    assert(!ReedwakeAnimateReaction() && gSprites[1].x2 == 3 && gSprites[1].y2 == -2);
    ReedwakeReact(1, RW_DODGE, RW_BEHIND);
    assert(strstr((const char *)lastMessage, "Your Aipom dodged!"));
    assert(strstr((const char *)lastMessage, "\nFoe Pound"));
    ReedwakeReset();
    assert(gPlttBufferUnfaded[15] == 0x7FFF);
    Setup(MOVE_TACKLE, MOVE_POUND);
    assert(ReedwakeSetQueue(0, slots, aim, 2));
    ReedwakeStart();
    assert(ReedwakeAdvance() && !sTimeline.prompt);
    sTimeline.started = FALSE;
    assert(ReedwakeAdvance() && sTimeline.prompt && gBattle_BG0_Y != 0);
    FinishSlide();
    keys = DPAD_DOWN;
    assert(ReedwakeAdvance() && sTimeline.menuCursor == RW_DODGE);
    keys = A_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.menuPage == 1);
    keys = B_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.menuPage == 0);
    keys = DPAD_RIGHT;
    assert(ReedwakeAdvance() && sTimeline.menuCursor == RW_TAKE_HIT);
    keys = A_BUTTON;
    assert(ReedwakeAdvance() && sTimeline.started && !sTimeline.menuVisible);
    assert(ReedwakeTimelineDamage(100) == 100 && gPlttBufferUnfaded[15] == sReedwakeGrey);
    ReedwakeReset();
    puts("Reedwake timeline checks passed.");
    return 0;
}
