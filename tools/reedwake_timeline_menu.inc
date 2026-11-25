static EWRAM_DATA u8 sReedwakeSlots[8] = {0};
static EWRAM_DATA u8 sReedwakePositions[8] = {0};
static EWRAM_DATA u8 sReedwakeCount = 0;
static EWRAM_DATA u8 sReedwakeAim = 0;
static const u8 sReedwakeQueueText[] = _("Q:");
static const u8 sReedwakeFront[] = _(" FRONT");
static const u8 sReedwakeAir[] = _(" AIR");
static const u8 sReedwakeBehind[] = _(" BEHIND");
static const u8 *const sReedwakeAimText[] = {sReedwakeFront, sReedwakeBehind, sReedwakeAir};
static const u8 sReedwakeAimValue[] = {0, 3, 2};

static void ReedwakeShowQueue(void)
{
    u8 *end = StringCopy(gDisplayedStringBattle, sReedwakeQueueText);
    end = ConvertIntToDecimalStringN(end, sReedwakeCount, STR_CONV_MODE_LEFT_ALIGN, 1);
    StringCopy(end, sReedwakeAimText[sReedwakeAim]);
    BattlePutTextOnWindow(gDisplayedStringBattle, B_WIN_MOVE_TYPE);
}

static bool8 ReedwakeMoveInput(const struct ChooseMoveStruct *moveInfo)
{
    u8 slot = gMoveSelectionCursor[gActiveBattler];
    u8 i, used = 0, limit = ReedwakeQueueLimit();
    u16 move = moveInfo->moves[slot];
    if (!limit)
        return FALSE;
    if (JOY_NEW(L_BUTTON))
    {
        for (i = 0; i < sReedwakeCount; i++)
            used += sReedwakeSlots[i] == slot;
        if (sReedwakeCount < limit && ReedwakeCanQueue(move) && used < moveInfo->currentPP[slot]
            && !((move == MOVE_DIG || move == MOVE_FLY) && sReedwakeCount + 1 == limit))
        {
            sReedwakeSlots[sReedwakeCount] = slot;
            sReedwakePositions[sReedwakeCount++] = sReedwakeAimValue[sReedwakeAim];
            PlaySE(SE_SELECT);
        }
        else
            PlaySE(SE_FAILURE);
        ReedwakeShowQueue();
        return TRUE;
    }
    if (JOY_NEW(R_BUTTON))
    {
        sReedwakeAim = (sReedwakeAim + 1) % ARRAY_COUNT(sReedwakeAimText);
        ReedwakeShowQueue();
        return TRUE;
    }
    if (sReedwakeCount && JOY_NEW(B_BUTTON))
    {
        sReedwakeCount--;
        ReedwakeShowQueue();
        return TRUE;
    }
    if (sReedwakeCount && JOY_NEW(START_BUTTON))
    {
        if (ReedwakeSetQueue(gActiveBattler, sReedwakeSlots, sReedwakePositions, sReedwakeCount))
        {
            u8 target = GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT);
            BtlController_EmitTwoReturnValues(B_COMM_TO_ENGINE, B_ACTION_EXEC_SCRIPT,
                sReedwakeSlots[0] | (target << 8));
            PlayerBufferExecCompleted();
        }
        return TRUE;
    }
    return FALSE;
}
