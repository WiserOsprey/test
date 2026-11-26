/* Optional single-battle timeline. Normal turns never call the scheduler. */
enum { RW_FRONT, RW_UNDER, RW_AIR, RW_BEHIND };
enum { RW_ATTACK, RW_DEFEND, RW_DODGE, RW_TAKE_HIT };
enum { RW_FAST_LIMIT = 25, RW_SPEED_UNAVAILABLE = 0xFF };

struct ReedwakeTimeline
{
    u8 queue[2][8], aim[8], count[2], next[2], position[2], boost[2], party[2];
    u16 clock[2], now;
    s16 reactionX, reactionY;
    u8 animationFrame, animationSprite, animationKind, animationBattler, animationPosition;
    u8 closingAction, staggered;
    u8 menuFrame, menuCursor, menuPage;
    bool8 menuVisible;
    u16 menuBorder, menuPaper;
    u8 requested, active, started, prompt, incoming, percent, guardRecoil, dug[2], fly[2];
};
static EWRAM_DATA struct ReedwakeTimeline sTimeline = {0};
static EWRAM_DATA u8 sReedwakeMessage[128] = {0};
static EWRAM_DATA bool8 sReedwakeTinted = FALSE;
static EWRAM_DATA u16 sReedwakeSavedBackground = 0;
static const u16 sReedwakeGrey = RGB(27, 27, 27);
static const u8 sTimelineYour[] = _("Your ");
static const u8 sTimelineFoe[] = _("Foe ");
static const u8 sTimelineLine[] = _("\n");
static const u8 sTimelineClash[] = _(" clashed!");
static const u8 sTimelineGuard[] = _(" guarded!");
static const u8 sTimelineDodge[] = _(" dodged!");
static const u8 *const sTimelineReactionText[] = {sTimelineClash, sTimelineGuard, sTimelineDodge};
static const u8 sTimelinePrompt[] = _(" incoming!");
static const u8 sTimelineWeak[] = _(" hits harder!");
static const u8 sTimelineStopped[] = _(" was blocked!");
static const u8 sTimelineDig[] = _("Burrowed underground!");
static const u8 sTimelineFly[] = _("Rose into the air!");
static const u8 sTimelineBlock[] = _("The attack was blocked!");
static const u8 sTimelineStrong[] = _(" was overpowered!");
static const u8 sTimelineStagger[] = _("queue was staggered!");

void ReedwakeSetTextboxTint(bool8 tinted)
{
    /* The battle message window uses BG palette 0, color 15 as its paper. */
    if (tinted == sReedwakeTinted)
        return;
    if (tinted)
        sReedwakeSavedBackground = gPlttBufferUnfaded[15];
    LoadPalette(tinted ? &sReedwakeGrey : &sReedwakeSavedBackground, 15, sizeof(u16));
    sReedwakeTinted = tinted;
}

static const u16 sReactionBorder = RGB(23, 10, 3);
static const u16 sReactionPaper = RGB(31, 31, 31);
static const u16 sReactionSelected = RGB(31, 29, 22);
static const u8 sReactionColors[] = {0, 1, 0};
static const u8 sReactionClash[] = _("CLASH");
static const u8 sReactionGuard[] = _("GUARD");
static const u8 sReactionDodge[] = _("DODGE");
static const u8 sReactionTakeHit[] = _("TAKE HIT");
static const u8 sReactionFront[] = _("FRONT");
static const u8 sReactionAir[] = _("AIR");
static const u8 sReactionUnder[] = _("UNDER");
static const u8 sReactionBehind[] = _("BEHIND");
static const u8 sReactionPosition[] = _("Dodge where?");
static const u8 *const sReactionOptions[2][4] = {
    {sReactionClash, sReactionGuard, sReactionDodge, sReactionTakeHit},
    {sReactionFront, sReactionAir, sReactionUnder, sReactionBehind},
};
static const u8 sReactionPositions[] = {RW_FRONT, RW_AIR, RW_UNDER, RW_BEHIND};
static const u8 sReactionSlide[] = {22, 16, 11, 7, 4, 2, 0};

static void ReedwakeDrawReactionMenu(void)
{
    u8 i;
    const u8 *title = sTimeline.menuPage ? sReactionPosition : sReedwakeMessage;
    LoadPalette(&sReactionSelected, 15, sizeof(u16));
    LoadPalette(&sReactionPaper, 14, sizeof(u16));
    FillWindowPixelBuffer(B_WIN_MSG, PIXEL_FILL(13));
    FillWindowPixelRect(B_WIN_MSG, PIXEL_FILL(14), 1, 1, 206, 9);
    AddTextPrinterParameterized4(B_WIN_MSG, FONT_SMALL, 5, 0, 0, 0, sReactionColors, 0, title);
    for (i = 0; i < 4; i++)
    {
        u8 x = 1 + (i & 1) * 104;
        u8 y = 11 + (i / 2) * 10;
        FillWindowPixelRect(B_WIN_MSG, PIXEL_FILL(i == sTimeline.menuCursor ? 15 : 14), x, y, 102, 9);
        AddTextPrinterParameterized4(B_WIN_MSG, FONT_SMALL, x + 5, y - 1,
                                    0, 0, sReactionColors, 0, sReactionOptions[sTimeline.menuPage][i]);
    }
    PutWindowTilemap(B_WIN_MSG);
    CopyWindowToVram(B_WIN_MSG, COPYWIN_FULL);
}

static void ReedwakeOpenReactionMenu(u16 move)
{
    sTimeline.menuBorder = gPlttBufferUnfaded[13];
    sTimeline.menuPaper = gPlttBufferUnfaded[14];
    sTimeline.menuFrame = 0;
    sTimeline.menuCursor = 0;
    sTimeline.menuPage = 0;
    sTimeline.menuVisible = TRUE;
    LoadPalette(&sReactionBorder, 13, sizeof(u16));
    StringCopy(StringCopy(StringCopy(sReedwakeMessage, sTimelineFoe), gMoveNames[move]), sTimelinePrompt);
    gBattle_BG0_Y = 0 - sReactionSlide[0];
    PlaySE(SE_SELECT);
    ReedwakeDrawReactionMenu();
}

static void ReedwakeCloseReactionMenu(void)
{
    if (!sTimeline.menuVisible)
        return;
    LoadPalette(&sTimeline.menuBorder, 13, sizeof(u16));
    LoadPalette(&sTimeline.menuPaper, 14, sizeof(u16));
    LoadPalette(&sReedwakeGrey, 15, sizeof(u16));
    gBattle_BG0_Y = 0;
    sTimeline.menuVisible = FALSE;
}

static void ReedwakeStartReactionAnimation(u8 battler, u8 kind)
{
    u8 spriteId = gBattlerSpriteIds[battler];
    if (spriteId >= MAX_SPRITES || !gSprites[spriteId].inUse)
        return;
    sTimeline.animationSprite = spriteId;
    sTimeline.animationKind = kind;
    sTimeline.animationBattler = battler;
    sTimeline.animationPosition = sTimeline.position[battler];
    sTimeline.reactionX = gSprites[spriteId].x2;
    sTimeline.reactionY = gSprites[spriteId].y2;
    sTimeline.animationFrame = 1;
}

static bool8 ReedwakeAnimateReaction(void)
{
    struct Sprite *sprite;
    s16 distance, direction, x = 0, y = 0;
    u8 frame = sTimeline.animationFrame;
    if (!frame)
        return FALSE;
    sprite = &gSprites[sTimeline.animationSprite];
    if (!sprite->inUse)
    {
        sTimeline.animationFrame = 0;
        return FALSE;
    }
    if (frame == 17)
    {
        sprite->x2 = sTimeline.reactionX;
        sprite->y2 = sTimeline.reactionY;
        sTimeline.animationFrame = 0;
        return FALSE;
    }
    distance = frame <= 8 ? frame : 17 - frame;
    direction = sTimeline.animationBattler == 0 ? 1 : -1;
    if (sTimeline.animationKind == RW_ATTACK)
    {
        x = distance * 2 * direction;
        y = -(distance / 2);
    }
    else if (sTimeline.animationKind == RW_DEFEND)
    {
        x = (frame % 4 < 2 ? 1 : -1) * direction;
        y = distance / 2;
    }
    else
    {
        x = -distance * 2 * direction;
        y = sTimeline.animationPosition == RW_UNDER ? distance : -distance;
    }
    sprite->x2 = sTimeline.reactionX + x;
    sprite->y2 = sTimeline.reactionY + y;
    sTimeline.animationFrame++;
    return TRUE;
}

static const u8 *ReedwakeSideText(u8 battler)
{
    return battler == 0 ? sTimelineYour : sTimelineFoe;
}

static void ReedwakePrintReaction(u8 incoming, u8 reaction, u16 move, const u8 *outcome, u8 staggered)
{
    u8 defender = incoming ^ 1;
    u8 *text = StringCopy(sReedwakeMessage, ReedwakeSideText(defender));
    text = StringCopy_Nickname(text, gBattleMons[defender].nickname);
    text = StringCopy(text, sTimelineReactionText[reaction]);
    text = StringCopy(text, sTimelineLine);
    if (staggered < 2)
        StringCopy(StringCopy(text, ReedwakeSideText(staggered)), sTimelineStagger);
    else
        StringCopy(StringCopy(StringCopy(text, ReedwakeSideText(incoming)), gMoveNames[move]), outcome);
    BattlePutTextOnWindow(sReedwakeMessage, B_WIN_MSG);
}

static void ReedwakeReset(void)
{
    ReedwakeCloseReactionMenu();
    ReedwakeSetTextboxTint(FALSE);
    memset(&sTimeline, 0, sizeof(sTimeline));
}

u8 ReedwakeQueueLimit(void)
{
    u16 flag;
    u8 count = 0;
    if (gBattlersCount != 2
        || gBattleTypeFlags & (BATTLE_TYPE_DOUBLE | BATTLE_TYPE_LINK | BATTLE_TYPE_RECORDED | BATTLE_TYPE_FRONTIER | BATTLE_TYPE_SAFARI | BATTLE_TYPE_WALLY_TUTORIAL))
        return 0;
    for (flag = FLAG_BADGE01_GET; flag <= FLAG_BADGE08_GET; flag++)
        if (FlagGet(flag))
            count++;
    return count;
}

static bool8 ReedwakeCharge(u16 move)
{
    return move == MOVE_DIG || move == MOVE_FLY;
}

static u8 ReedwakeDelay(u16 move)
{
    u8 power = gBattleMoves[move].power;
    if (gBattleMoves[move].priority > 0)
        return 0;
    if (gBattleMoves[move].priority < 0)
        return 100;
    switch (gBattleMoves[move].effect)
    {
    case EFFECT_RAZOR_WIND:
    case EFFECT_SKY_ATTACK:
    case EFFECT_SKULL_BASH:
    case EFFECT_SOLAR_BEAM:
    case EFFECT_RECHARGE:
        return 100;
    }
    if (move == MOVE_TACKLE || move == MOVE_POUND)
        return RW_FAST_LIMIT;
    if (power >= 95)
        return 100;
    if (power >= 85)
        return 75;
    return 50;
}

bool8 ReedwakeCanQueue(u16 move)
{
    return move > MOVE_NONE && move < MOVES_COUNT;
}

u8 ReedwakeTimelineTarget(u8 battler, u16 move)
{
    if (move == MOVE_CURSE)
        return (gBattleMons[battler].types[0] == TYPE_GHOST
             || gBattleMons[battler].types[1] == TYPE_GHOST) ? battler ^ 1 : battler;
    if (gBattleMoves[move].target & (MOVE_TARGET_USER | MOVE_TARGET_USER_OR_SELECTED))
        return battler;
    return battler ^ 1;
}

static bool8 ReedwakeIsAttack(u8 battler, u16 move)
{
    return gBattleMoves[move].power && ReedwakeTimelineTarget(battler, move) != battler;
}

static bool8 ReedwakeNeedsStockTurn(u8 battler)
{
    return (gBattleMons[battler].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE)) != 0;
}

u8 ReedwakeMoveSpeed(u16 move)
{
    return ReedwakeCanQueue(move) ? ReedwakeDelay(move) : RW_SPEED_UNAVAILABLE;
}

void ReedwakeCancelQueue(void)
{
    sTimeline.requested = 0;
}

bool8 ReedwakeSetQueue(u8 battler, const u8 *slots, const u8 *positions, u8 count)
{
    u8 i;
    if (!count || count > ReedwakeQueueLimit())
        return FALSE;
    for (i = 0; i < count; i++)
    {
        u16 move;
        if (slots[i] >= 4)
            return FALSE;
        move = gBattleMons[battler].moves[slots[i]];
        if (!ReedwakeCanQueue(move) || (ReedwakeCharge(move) && i + 1 == ReedwakeQueueLimit()))
            return FALSE;
    }
    sTimeline.requested = count;
    for (i = 0; i < count; i++)
    {
        sTimeline.queue[0][i] = slots[i];
        sTimeline.aim[i] = positions[i];
    }
    return TRUE;
}

static bool8 ReedwakeHasType(u8 battler, u8 type)
{
    return gBattleMons[battler].types[0] == type || gBattleMons[battler].types[1] == type;
}

static u32 ReedwakeSpeed(u8 battler)
{
    u32 speed = gBattleMons[battler].speed;
    u8 stage = gBattleMons[battler].statStages[STAT_SPEED];
    speed = speed * gStatStageRatios[stage][0] / gStatStageRatios[stage][1];
    if (gBattleMons[battler].status1 & STATUS1_PARALYSIS)
        speed /= 4;
    if ((sTimeline.position[battler] == RW_AIR && ReedwakeHasType(battler, TYPE_FLYING))
     || (sTimeline.position[battler] == RW_UNDER && ReedwakeHasType(battler, TYPE_GROUND))
     || (sTimeline.position[battler] == RW_BEHIND && ReedwakeHasType(battler, TYPE_DARK)))
        speed = speed * 5 / 4;
    return max(speed, 1);
}

static bool8 ReedwakeCanReact(u8 defender, u8 attacker)
{
    /* A battler can react at two thirds of the incoming attacker's Speed. */
    return ReedwakeSpeed(defender) * 3 >= ReedwakeSpeed(attacker) * 2;
}

static u16 ReedwakeMove(u8 battler)
{
    return gBattleMons[battler].moves[sTimeline.queue[battler][sTimeline.next[battler]]];
}

static void ReedwakePlanOpponent(u8 count)
{
    u8 preferred = gBattleStruct->chosenMovePositions[1];
    u8 remaining[4];
    u8 pick, slot, i, step;
    u16 move;

    memcpy(remaining, gBattleMons[1].pp, sizeof(remaining));
    sTimeline.count[1] = count;
    for (i = 0; i < count; i++)
    {
        pick = 4;
        for (step = 0; step < 4; step++)
        {
            slot = (preferred + step) % 4;
            move = gBattleMons[1].moves[slot];
            if (!remaining[slot] || !ReedwakeCanQueue(move)
             || (ReedwakeCharge(move) && i + 1 == count))
                continue;
            pick = slot;
            break;
        }
        sTimeline.queue[1][i] = pick;
        if (pick == 4)
            continue;
        remaining[pick]--;
        if (ReedwakeCharge(gBattleMons[1].moves[pick]))
            sTimeline.queue[1][++i] = pick;
    }
}

static void ReedwakeStart(void)
{
    u8 i, count = sTimeline.requested;
    sTimeline.requested = 0;
    if (!count || gChosenActionByBattler[0] != B_ACTION_USE_MOVE
        || gChosenActionByBattler[1] != B_ACTION_USE_MOVE)
    {
        ReedwakeReset();
        return;
    }
    for (i = 0; i < 2; i++)
    {
        if (ReedwakeNeedsStockTurn(i)
         || gDisableStructs[i].encoredMove || gProtectStructs[i].noValidMoves)
        {
            ReedwakeReset();
            return;
        }
        sTimeline.party[i] = gBattlerPartyIndexes[i];
    }
    sTimeline.active = TRUE;
    ReedwakeSetTextboxTint(TRUE);
    gBattle_BG0_X = 0;
    gBattle_BG0_Y = 0;
    sTimeline.count[0] = count;
    if (ReedwakeCharge(gBattleMons[0].moves[sTimeline.queue[0][count - 1]]))
    {
        sTimeline.queue[0][count] = sTimeline.queue[0][count - 1];
        sTimeline.aim[count] = RW_FRONT;
        sTimeline.count[0]++;
    }
    ReedwakePlanOpponent(sTimeline.count[0]);
}

static bool8 ReedwakeReady(u8 battler)
{
    /* The engine resolves mandatory continuation or recharge on ordinary turns. */
    if (ReedwakeNeedsStockTurn(battler))
    {
        sTimeline.next[battler] = sTimeline.count[battler];
        return FALSE;
    }
    while (sTimeline.next[battler] < sTimeline.count[battler])
    {
        u8 slot = sTimeline.queue[battler][sTimeline.next[battler]];
        if (slot < 4 && gBattleMons[battler].pp[slot])
            return TRUE;
        sTimeline.next[battler]++;
    }
    return FALSE;
}

static u16 ReedwakeDue(u8 battler)
{
    return max(sTimeline.now, sTimeline.clock[battler] + ReedwakeDelay(ReedwakeMove(battler)));
}

static void ReedwakeApplyPosition(u8 battler, u16 move, u8 aim)
{
    if (aim == RW_FRONT || aim == RW_BEHIND)
        sTimeline.position[battler] = aim;
    if (aim == RW_AIR && (move == MOVE_WING_ATTACK || move == MOVE_AERIAL_ACE))
        sTimeline.position[battler] = RW_AIR;
}

static void ReedwakeAction(u8 battler, u8 multiplier)
{
    u8 index = sTimeline.next[battler]++;
    u8 slot = sTimeline.queue[battler][index];
    u16 move = gBattleMons[battler].moves[slot];
    u8 other = battler ^ 1;
    bool8 attacks = ReedwakeIsAttack(battler, move);
    sTimeline.clock[battler] = sTimeline.now;
    if (ReedwakeCharge(move) && !sTimeline.dug[battler] && !sTimeline.fly[battler])
    {
        sTimeline.position[battler] = move == MOVE_DIG ? RW_UNDER : RW_AIR;
        sTimeline.dug[battler] = move == MOVE_DIG;
        sTimeline.fly[battler] = move == MOVE_FLY;
        BattlePutTextOnWindow(move == MOVE_DIG ? sTimelineDig : sTimelineFly, B_WIN_MSG);
        return;
    }
    if (battler == 0 && !sTimeline.dug[battler] && !sTimeline.fly[battler])
        ReedwakeApplyPosition(battler, move, sTimeline.aim[index]);
    if (attacks && sTimeline.position[battler] == RW_BEHIND && ReedwakeDelay(move) <= RW_FAST_LIMIT)
        multiplier = multiplier * 5 / 4;
    if (attacks && sTimeline.boost[battler])
    {
        multiplier = multiplier * 5 / 4;
        sTimeline.boost[battler] = FALSE;
    }
    sTimeline.percent = multiplier;
    sTimeline.guardRecoil = FALSE;
    gBattlerByTurnOrder[0] = battler;
    gBattlerByTurnOrder[1] = other;
    gActionsByTurnOrder[0] = B_ACTION_USE_MOVE;
    gActionsByTurnOrder[1] = B_ACTION_FINISHED;
    gBattleStruct->chosenMovePositions[battler] = slot;
    gChosenMoveByBattler[battler] = move;
    gBattleStruct->moveTarget[battler] = ReedwakeTimelineTarget(battler, move);
    gCurrentTurnActionNumber = 0;
    gCurrentActionFuncId = B_ACTION_USE_MOVE;
    sTimeline.started = TRUE;
}

s32 ReedwakeTimelineDamage(s32 damage)
{
    if (!sTimeline.active)
        return damage;
    return max(1, damage * sTimeline.percent / 100);
}


bool8 ReedwakeGuardRecoil(void)
{
    if (!sTimeline.active || !sTimeline.started || !sTimeline.guardRecoil)
        return FALSE;
    /* Recoil is dispatched once even if moveend runs more than once. */
    sTimeline.guardRecoil = FALSE;
    return TRUE;
}

bool8 ReedwakeReleaseCharge(void)
{
    return sTimeline.active && sTimeline.started && (sTimeline.dug[gBattlerAttacker] || sTimeline.fly[gBattlerAttacker]);
}

void ReedwakePositionHit(void)
{
    if (!sTimeline.active || !sTimeline.started)
        return;
    if (sTimeline.dug[gBattlerAttacker] && !(gMoveResultFlags & MOVE_RESULT_NO_EFFECT)
        && gBattlerTarget != gBattlerAttacker && gBattleMoves[gCurrentMove].power)
        sTimeline.position[gBattlerTarget] = RW_AIR;
    if (sTimeline.dug[gBattlerAttacker] || sTimeline.fly[gBattlerAttacker])
        sTimeline.position[gBattlerAttacker] = RW_FRONT;
    sTimeline.dug[gBattlerAttacker] = sTimeline.fly[gBattlerAttacker] = FALSE;
}

static void ReedwakeDrop(u8 battler)
{
    sTimeline.clock[battler] = sTimeline.now;
    sTimeline.next[battler]++;
}

static void ReedwakeReact(u8 incoming, u8 reaction, u8 position)
{
    u8 defender = incoming ^ 1;
    u16 move = ReedwakeMove(incoming);
    u32 strength, pressure, score;
    bool8 clash = reaction == RW_ATTACK && ReedwakeReady(defender)
                && ReedwakeIsAttack(defender, ReedwakeMove(defender))
                && !ReedwakeCharge(ReedwakeMove(defender));
    if (reaction == RW_ATTACK && !clash)
        reaction = RW_DEFEND;
    if (reaction == RW_DODGE)
    {
        if (position == RW_FRONT || position == RW_BEHIND
         || (position == RW_AIR && (ReedwakeHasType(defender, TYPE_FLYING) || sTimeline.fly[defender]))
         || (position == RW_UNDER && sTimeline.dug[defender]))
            sTimeline.position[defender] = position;
        strength = ReedwakeSpeed(defender) * 100;
        pressure = ReedwakeSpeed(incoming) * (gBattleMoves[move].accuracy ? gBattleMoves[move].accuracy : 100);
        if ((move == MOVE_EARTHQUAKE || move == MOVE_MAGNITUDE) && sTimeline.position[defender] == RW_AIR)
            strength = pressure * 2;
    }
    else
    {
        strength = reaction == RW_ATTACK ? gBattleMons[defender].attack : gBattleMons[defender].defense;
        pressure = gBattleMons[incoming].attack;
    }
    score = strength * 100 / max(pressure, 1);
    ReedwakeStartReactionAnimation(defender, reaction);
    if (score < 85)
    {
        if (clash)
            ReedwakeDrop(defender);
        if (Random() % 64 == 0)
        {
            sTimeline.next[defender] = sTimeline.count[defender];
            sTimeline.staggered |= 1 << defender;
            ReedwakePrintReaction(incoming, reaction, move, sTimelineWeak, defender);
        }
        else
            ReedwakePrintReaction(incoming, reaction, move, sTimelineWeak, 2);
        ReedwakeAction(incoming, 125);
    }
    else if (score < 125)
    {
        ReedwakeDrop(incoming);
        if (clash)
            ReedwakeDrop(defender);
        ReedwakePrintReaction(incoming, reaction, move, sTimelineStopped, 2);
    }
    else
    {
        bool8 stagger = Random() % 64 == 0;
        ReedwakePrintReaction(incoming, reaction, move, sTimelineStrong, stagger ? incoming : 2);
        if (reaction == RW_ATTACK)
        {
            ReedwakeDrop(incoming);
            ReedwakeAction(defender, 150);
        }
        else if (reaction == RW_DEFEND)
        {
            ReedwakeAction(incoming, 35);
            sTimeline.guardRecoil = TRUE;
        }
        else
        {
            ReedwakeDrop(incoming);
            sTimeline.boost[defender] = TRUE;
        }
        if (stagger)
        {
            sTimeline.next[incoming] = sTimeline.count[incoming];
            sTimeline.staggered |= 1 << incoming;
        }
    }
}

/* Return TRUE while waiting for input, or when the next action was installed. */
static bool8 ReedwakeAdvance(void)
{
    bool8 ready0, ready1;
    u8 actor, reaction, position = RW_FRONT;
    u16 move;
    if (!sTimeline.active)
        return FALSE;
    if (gBattleOutcome || !gBattleMons[0].hp || !gBattleMons[1].hp
     || sTimeline.party[0] != gBattlerPartyIndexes[0] || sTimeline.party[1] != gBattlerPartyIndexes[1])
        return FALSE;
    if (gBattleControllerExecFlags)
        return TRUE;
    if (IsTextPrinterActive(B_WIN_MSG))
        return TRUE;
    if (sTimeline.prompt)
    {
        u8 cursor = sTimeline.menuCursor;
        if (sTimeline.menuFrame < ARRAY_COUNT(sReactionSlide) - 1)
        {
            gBattle_BG0_Y = 0 - sReactionSlide[++sTimeline.menuFrame];
            return TRUE;
        }
        if (JOY_NEW(DPAD_LEFT | DPAD_RIGHT))
            cursor ^= 1;
        else if (JOY_NEW(DPAD_UP | DPAD_DOWN))
            cursor ^= 2;
        if (cursor != sTimeline.menuCursor)
        {
            sTimeline.menuCursor = cursor;
            ReedwakeDrawReactionMenu();
            return TRUE;
        }
        if (sTimeline.menuPage && JOY_NEW(B_BUTTON))
        {
            sTimeline.menuPage = 0;
            sTimeline.menuCursor = RW_DODGE;
            ReedwakeDrawReactionMenu();
            return TRUE;
        }
        if (!sTimeline.menuPage && JOY_NEW(R_BUTTON))
            reaction = RW_DODGE;
        else if (!sTimeline.menuPage && JOY_NEW(B_BUTTON))
            reaction = RW_DEFEND;
        else if (!JOY_NEW(A_BUTTON))
            return TRUE;
        else if (sTimeline.menuPage)
        {
            reaction = RW_DODGE;
            position = sReactionPositions[cursor];
        }
        else if (cursor == RW_DODGE)
        {
            sTimeline.menuPage = 1;
            sTimeline.menuCursor = 0;
            ReedwakeDrawReactionMenu();
            return TRUE;
        }
        else
            reaction = cursor;

        sTimeline.prompt = FALSE;
        ReedwakeCloseReactionMenu();
        if (reaction == RW_TAKE_HIT)
            ReedwakeAction(sTimeline.incoming, 100);
        else
            ReedwakeReact(sTimeline.incoming, reaction, position);
        return TRUE;
    }
    ready0 = ReedwakeReady(0);
    ready1 = ReedwakeReady(1);
    if (sTimeline.closingAction || (!ready0 && !ready1))
        return FALSE;
    if (ready0 && ready1)
    {
        u16 playerDue = ReedwakeDue(0);
        u16 opponentDue = ReedwakeDue(1);
        actor = opponentDue < playerDue
             || (opponentDue == playerDue && ReedwakeSpeed(1) > ReedwakeSpeed(0));
    }
    else
    {
        actor = ready1;
        if (!(sTimeline.staggered & (1 << (actor ^ 1))))
            sTimeline.closingAction = TRUE;
    }
    sTimeline.now = ReedwakeDue(actor);
    move = ReedwakeMove(actor);
    if ((move == MOVE_EARTHQUAKE || move == MOVE_MAGNITUDE) && sTimeline.position[actor ^ 1] == RW_AIR)
    {
        ReedwakeDrop(actor);
        BattlePutTextOnWindow(sTimelineBlock, B_WIN_MSG);
        return TRUE;
    }
    if (sTimeline.position[actor ^ 1] == RW_UNDER && ReedwakeIsAttack(actor, move) && !ReedwakeCharge(move)
        && move != MOVE_EARTHQUAKE && move != MOVE_MAGNITUDE)
    {
        ReedwakeDrop(actor);
        BattlePutTextOnWindow(sTimelineBlock, B_WIN_MSG);
        return TRUE;
    }
    if (actor == 0 && ReedwakeIsAttack(actor, move) && !ReedwakeCharge(move)
        && ReedwakeCanReact(1, 0) && Random() % 5 == 0)
    {
        if (ReedwakeHasType(1, TYPE_FLYING) && (move == MOVE_EARTHQUAKE || move == MOVE_MAGNITUDE))
            ReedwakeReact(actor, RW_DODGE, RW_AIR);
        else if (ReedwakeReady(1) && gBattleMons[1].attack > gBattleMons[1].defense)
            ReedwakeReact(actor, RW_ATTACK, RW_FRONT);
        else if (gBattleMons[1].speed > gBattleMons[1].defense)
            ReedwakeReact(actor, RW_DODGE, RW_BEHIND);
        else
            ReedwakeReact(actor, RW_DEFEND, RW_FRONT);
        return TRUE;
    }
    if (actor == 1 && ReedwakeIsAttack(actor, move) && (!ReedwakeCharge(move) || sTimeline.dug[1] || sTimeline.fly[1]) && ReedwakeCanReact(0, 1))
    {
        sTimeline.incoming = actor;
        sTimeline.prompt = TRUE;
        ReedwakeOpenReactionMenu(move);
    }
    else
        ReedwakeAction(actor, 100);
    return TRUE;
}
