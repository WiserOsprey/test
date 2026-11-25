/* Optional single-battle timeline. Normal turns never call the scheduler. */
enum { RW_FRONT, RW_UNDER, RW_AIR, RW_BEHIND };
enum { RW_ATTACK, RW_DEFEND, RW_DODGE };

struct ReedwakeTimeline
{
    u8 queue[2][8], aim[8], count[2], next[2], clock[2], position[2], boost[2], party[2];
    u8 requested, active, started, prompt, incoming, percent, dug[2], fly[2];
};
static EWRAM_DATA struct ReedwakeTimeline sTimeline = {0};
static const u8 sTimelinePrompt[] = _(" incoming!\nA: Clash  B: Guard  R/Arrows: Dodge");
static const u8 sTimelineWeak[] = _("The reaction was too weak!");
static const u8 sTimelineCharge[] = _("Changed battle position!");
static const u8 sTimelineBlock[] = _("The attack was blocked!");
static const u8 sTimelineStrong[] = _("The reaction overpowered the move!");
static const u8 sTimelineStagger[] = _("Staggered! The remaining queue fell apart!");

static void ReedwakeReset(void)
{
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

static u8 ReedwakeTicks(u16 move)
{
    if (move == MOVE_TACKLE || move == MOVE_POUND || gBattleMoves[move].priority > 0)
        return 1;
    return gBattleMoves[move].power >= 85 ? 3 : 2;
}

bool8 ReedwakeCanQueue(u16 move)
{
    switch (move)
    {
    case MOVE_TACKLE: case MOVE_POUND: case MOVE_SCRATCH: case MOVE_QUICK_ATTACK:
    case MOVE_WING_ATTACK: case MOVE_AERIAL_ACE: case MOVE_METAL_CLAW:
    case MOVE_EARTHQUAKE: case MOVE_MAGNITUDE: case MOVE_ROCK_THROW:
    case MOVE_WATER_GUN: case MOVE_SURF: case MOVE_EMBER: case MOVE_FLAMETHROWER:
    case MOVE_BITE: case MOVE_SPARK: case MOVE_THUNDER_SHOCK: case MOVE_SHOCK_WAVE:
    case MOVE_ICE_BEAM: case MOVE_VINE_WHIP: case MOVE_RAZOR_LEAF:
    case MOVE_DIG: case MOVE_FLY:
        return TRUE;
    default:
        return FALSE;
    }
}

bool8 ReedwakeSetQueue(u8 battler, const u8 *slots, const u8 *positions, u8 count)
{
    u8 i;
    if (!count || count > ReedwakeQueueLimit())
        return FALSE;
    for (i = 0; i < count; i++)
    {
        u16 move = gBattleMons[battler].moves[slots[i]];
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
    return gBattleMons[battler].type1 == type || gBattleMons[battler].type2 == type;
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

static u16 ReedwakeMove(u8 battler)
{
    return gBattleMons[battler].moves[sTimeline.queue[battler][sTimeline.next[battler]]];
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
        if (gBattleMons[i].status2 & (STATUS2_MULTIPLETURNS | STATUS2_RECHARGE)
         || gDisableStructs[i].encoredMove || gProtectStructs[i].noValidMoves)
        {
            ReedwakeReset();
            return;
        }
        sTimeline.party[i] = gBattlerPartyIndexes[i];
    }
    sTimeline.active = TRUE;
    gBattle_BG0_X = 0;
    gBattle_BG0_Y = 0;
    sTimeline.count[0] = count;
    if (ReedwakeCharge(gBattleMons[0].moves[sTimeline.queue[0][count - 1]]))
    {
        sTimeline.queue[0][count] = sTimeline.queue[0][count - 1];
        sTimeline.aim[count] = RW_FRONT;
        sTimeline.count[0]++;
    }
    sTimeline.queue[1][0] = gBattleStruct->chosenMovePositions[1];
    sTimeline.count[1] = ReedwakeCharge(gChosenMoveByBattler[1]) ? 2 : 1;
    sTimeline.queue[1][1] = sTimeline.queue[1][0];
    if ((gBattleTypeFlags & BATTLE_TYPE_TRAINER) && count >= 3
        && gBattleMoves[gChosenMoveByBattler[1]].power && ReedwakeCanQueue(gChosenMoveByBattler[1]))
        sTimeline.count[1] = 2;
}

static bool8 ReedwakeReady(u8 battler)
{
    while (sTimeline.next[battler] < sTimeline.count[battler])
    {
        if (gBattleMons[battler].pp[sTimeline.queue[battler][sTimeline.next[battler]]])
            return TRUE;
        sTimeline.next[battler]++;
    }
    return FALSE;
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
    sTimeline.clock[battler] += ReedwakeTicks(move);
    if (ReedwakeCharge(move) && !sTimeline.dug[battler] && !sTimeline.fly[battler])
    {
        sTimeline.position[battler] = move == MOVE_DIG ? RW_UNDER : RW_AIR;
        sTimeline.dug[battler] = move == MOVE_DIG;
        sTimeline.fly[battler] = move == MOVE_FLY;
        BattlePutTextOnWindow(sTimelineCharge, B_WIN_MSG);
        return;
    }
    if (battler == 0 && !sTimeline.dug[battler] && !sTimeline.fly[battler])
        ReedwakeApplyPosition(battler, move, sTimeline.aim[index]);
    if (sTimeline.position[battler] == RW_BEHIND && ReedwakeTicks(move) == 1)
        multiplier = multiplier * 5 / 4;
    if (sTimeline.boost[battler])
    {
        multiplier = multiplier * 5 / 4;
        sTimeline.boost[battler] = FALSE;
    }
    sTimeline.percent = multiplier;
    gBattlerByTurnOrder[0] = battler;
    gBattlerByTurnOrder[1] = other;
    gActionsByTurnOrder[0] = B_ACTION_USE_MOVE;
    gActionsByTurnOrder[1] = B_ACTION_FINISHED;
    gBattleStruct->chosenMovePositions[battler] = slot;
    gChosenMoveByBattler[battler] = move;
    gBattleStruct->moveTarget[battler] = other;
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

bool8 ReedwakeReleaseCharge(void)
{
    return sTimeline.active && sTimeline.started && (sTimeline.dug[gBattlerAttacker] || sTimeline.fly[gBattlerAttacker]);
}

void ReedwakePositionHit(void)
{
    if (!sTimeline.active || !sTimeline.started)
        return;
    if (sTimeline.dug[gBattlerAttacker] && !(gMoveResultFlags & MOVE_RESULT_NO_EFFECT)
        && gBattleMoves[gCurrentMove].power)
        sTimeline.position[gBattlerTarget] = RW_AIR;
    if (sTimeline.dug[gBattlerAttacker] || sTimeline.fly[gBattlerAttacker])
        sTimeline.position[gBattlerAttacker] = RW_FRONT;
    sTimeline.dug[gBattlerAttacker] = sTimeline.fly[gBattlerAttacker] = FALSE;
}

static void ReedwakeDrop(u8 battler)
{
    sTimeline.clock[battler] += ReedwakeTicks(ReedwakeMove(battler));
    sTimeline.next[battler]++;
}

static void ReedwakeReact(u8 incoming, u8 reaction, u8 position)
{
    u8 defender = incoming ^ 1;
    u16 move = ReedwakeMove(incoming);
    u32 strength, pressure, score;
    bool8 clash = reaction == RW_ATTACK && ReedwakeReady(defender)
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
    if (score < 85)
    {
        if (clash)
            ReedwakeDrop(defender);
        if (Random() % 64 == 0)
        {
            sTimeline.next[defender] = sTimeline.count[defender];
            BattlePutTextOnWindow(sTimelineStagger, B_WIN_MSG);
        }
        else
            BattlePutTextOnWindow(sTimelineWeak, B_WIN_MSG);
        ReedwakeAction(incoming, 125);
    }
    else if (score < 125)
    {
        ReedwakeDrop(incoming);
        if (clash)
            ReedwakeDrop(defender);
        BattlePutTextOnWindow(sTimelineBlock, B_WIN_MSG);
    }
    else
    {
        bool8 stagger = Random() % 64 == 0;
        BattlePutTextOnWindow(stagger ? sTimelineStagger : sTimelineStrong, B_WIN_MSG);
        if (reaction == RW_ATTACK)
        {
            ReedwakeDrop(incoming);
            ReedwakeAction(defender, 150);
        }
        else if (reaction == RW_DEFEND)
            ReedwakeAction(incoming, 35);
        else
        {
            ReedwakeDrop(incoming);
            sTimeline.boost[defender] = TRUE;
        }
        if (stagger)
            sTimeline.next[incoming] = sTimeline.count[incoming];
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
        if (JOY_NEW(DPAD_UP)) position = RW_AIR;
        else if (JOY_NEW(DPAD_DOWN)) position = RW_UNDER;
        else if (JOY_NEW(DPAD_RIGHT)) position = RW_BEHIND;
        if (JOY_NEW(A_BUTTON)) reaction = RW_ATTACK;
        else if (JOY_NEW(B_BUTTON)) reaction = RW_DEFEND;
        else if (JOY_NEW(R_BUTTON | DPAD_ANY)) reaction = RW_DODGE;
        else return TRUE;
        sTimeline.prompt = FALSE;
        ReedwakeReact(sTimeline.incoming, reaction, position);
        return TRUE;
    }
    ready0 = ReedwakeReady(0);
    ready1 = ReedwakeReady(1);
    if (!ready0 && !ready1)
        return FALSE;
    actor = ready1;
    if (ready0 && (!ready1
        || sTimeline.clock[0] + ReedwakeTicks(ReedwakeMove(0)) < sTimeline.clock[1] + ReedwakeTicks(ReedwakeMove(1))
        || (sTimeline.clock[0] + ReedwakeTicks(ReedwakeMove(0)) == sTimeline.clock[1] + ReedwakeTicks(ReedwakeMove(1))
          && ReedwakeSpeed(0) >= ReedwakeSpeed(1))))
        actor = 0;
    move = ReedwakeMove(actor);
    if ((move == MOVE_EARTHQUAKE || move == MOVE_MAGNITUDE) && sTimeline.position[actor ^ 1] == RW_AIR)
    {
        ReedwakeDrop(actor);
        BattlePutTextOnWindow(sTimelineBlock, B_WIN_MSG);
        return TRUE;
    }
    if (sTimeline.position[actor ^ 1] == RW_UNDER && gBattleMoves[move].power
        && move != MOVE_EARTHQUAKE && move != MOVE_MAGNITUDE)
    {
        ReedwakeDrop(actor);
        BattlePutTextOnWindow(sTimelineBlock, B_WIN_MSG);
        return TRUE;
    }
    if (actor == 0 && gBattleMoves[move].power && !ReedwakeCharge(move)
        && ReedwakeSpeed(1) * 2 >= ReedwakeSpeed(0) && Random() % 5 == 0)
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
    if (actor == 1 && gBattleMoves[move].power && !ReedwakeCharge(move) && ReedwakeSpeed(0) * 2 >= ReedwakeSpeed(1))
    {
        sTimeline.incoming = actor;
        sTimeline.prompt = TRUE;
        StringCopy(StringCopy(gDisplayedStringBattle, gMoveNames[move]), sTimelinePrompt);
        BattlePutTextOnWindow(gDisplayedStringBattle, B_WIN_MSG);
    }
    else
        ReedwakeAction(actor, 100);
    return TRUE;
}
