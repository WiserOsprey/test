#include "global.h"
#include "battle.h"
#include "battle_anim.h"
#include "bulbasaur_field_notes.h"
#include "data.h"
#include "event_data.h"
#include "party_menu.h"
#include "pokemon.h"
#include "reedwake_delta.h"
#include "string_util.h"
#include "constants/maps.h"
#include "constants/moves.h"
#include "constants/species.h"
#include "constants/vars.h"

enum
{
    DELTA_UNSUPPORTED,
    DELTA_READY,
    DELTA_TRIAL_REQUIRED,
    DELTA_ALREADY_CONVERTED,
    DELTA_GRASS_TRIAL_REQUIRED,
    DELTA_FIRE_TRIAL_REQUIRED,
    DELTA_WATER_TRIAL_REQUIRED,
};

static const struct
{
    u16 standard;
    u16 delta;
} sDeltaForms[] =
{
    /* Delta mapping */
};

struct StarterTrial
{
    u16 forms[3];
    u16 map;
    u8 moveType;
    u8 message;
};

static const struct StarterTrial sStarterTrials[] =
{
    {{SPECIES_TREECKO, SPECIES_GROVYLE, SPECIES_SCEPTILE}, MAP_ROUTE101, TYPE_GRASS, DELTA_GRASS_TRIAL_REQUIRED},
    {{SPECIES_TORCHIC, SPECIES_COMBUSKEN, SPECIES_BLAZIKEN}, MAP_ROUTE103, TYPE_FIRE, DELTA_FIRE_TRIAL_REQUIRED},
    {{SPECIES_MUDKIP, SPECIES_MARSHTOMP, SPECIES_SWAMPERT}, MAP_ROUTE102, TYPE_WATER, DELTA_WATER_TRIAL_REQUIRED},
};

static EWRAM_DATA u16 sBattleTrialMask = 0;

static s32 FindStarterTrial(u16 species)
{
    s32 trial;
    u8 stage;

    for (trial = 0; trial < ARRAY_COUNT(sStarterTrials); trial++)
    {
        for (stage = 0; stage < ARRAY_COUNT(sStarterTrials[trial].forms); stage++)
        {
            if (sStarterTrials[trial].forms[stage] == species)
                return trial;
        }
    }
    return -1;
}

void ReedwakeDelta_StartBattle(void)
{
    sBattleTrialMask = 0;
}

void ReedwakeDelta_RecordMove(u8 battler, u16 move)
{
    u8 slot;
    const struct StarterTrial *recipe;
    s32 trial;

    if (gBattleTypeFlags & (BATTLE_TYPE_LINK | BATTLE_TYPE_RECORDED | BATTLE_TYPE_FRONTIER
                            | BATTLE_TYPE_SAFARI | BATTLE_TYPE_WALLY_TUTORIAL | BATTLE_TYPE_TRAINER)
        || GetBattlerSide(battler) != B_SIDE_PLAYER || move >= MOVES_COUNT)
        return;

    slot = gBattlerPartyIndexes[battler];
    if (slot >= PARTY_SIZE)
        return;
    trial = FindStarterTrial(GetMonData(&gPlayerParty[slot], MON_DATA_SPECIES_OR_EGG));
    if (trial < 0 || (VarGet(VAR_REEDWAKE_STARTER_TRIALS) & (1 << trial)))
        return;

    recipe = &sStarterTrials[trial];
    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(recipe->map)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(recipe->map)
        && gBattleMoves[move].type == recipe->moveType)
        sBattleTrialMask |= 1 << trial;
}

void ReedwakeDelta_FinishBattle(void)
{
    if (sBattleTrialMask && gBattleOutcome == B_OUTCOME_WON)
        VarSet(VAR_REEDWAKE_STARTER_TRIALS, VarGet(VAR_REEDWAKE_STARTER_TRIALS) | sBattleTrialMask);
}

u16 ReedwakeDelta_GetStandardSpecies(u16 species)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sDeltaForms); i++)
    {
        if (sDeltaForms[i].delta == species)
            return sDeltaForms[i].standard;
    }

    return species;
}

static u16 GetDeltaSpecies(u16 species)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sDeltaForms); i++)
    {
        if (sDeltaForms[i].standard == species)
            return sDeltaForms[i].delta;
    }

    return SPECIES_NONE;
}

static u16 GetSelectedForm(struct Pokemon **selected, u16 *target)
{
    u16 species;
    s32 trial;

    if (gSpecialVar_0x8004 >= PARTY_SIZE)
        return DELTA_UNSUPPORTED;

    *selected = &gPlayerParty[gSpecialVar_0x8004];
    species = GetMonData(*selected, MON_DATA_SPECIES_OR_EGG);
    if (ReedwakeDelta_GetStandardSpecies(species) != species)
        return DELTA_ALREADY_CONVERTED;

    *target = GetDeltaSpecies(species);
    if (*target == SPECIES_NONE)
        return DELTA_UNSUPPORTED;

    if (species == SPECIES_BULBASAUR && !(BulbasaurNotes_GetUnlocks() & BULBASAUR_NOTES_DELTA))
        return DELTA_TRIAL_REQUIRED;
    trial = FindStarterTrial(species);
    if (trial >= 0 && !(VarGet(VAR_REEDWAKE_STARTER_TRIALS) & (1 << trial)))
        return sStarterTrials[trial].message;

    return DELTA_READY;
}

u16 ReedwakeDelta_CheckSelected(void)
{
    struct Pokemon *selected;
    u16 target;
    u16 result = GetSelectedForm(&selected, &target);

    if (result == DELTA_READY)
        GetMonNickname(selected, gStringVar1);
    return result;
}

u16 ReedwakeDelta_ConvertSelected(void)
{
    struct Pokemon *selected;
    u16 target;
    u8 abilitySlot = 0;

    if (GetSelectedForm(&selected, &target) != DELTA_READY)
        return FALSE;

    SetMonData(selected, MON_DATA_SPECIES, &target);
    SetMonData(selected, MON_DATA_ABILITY_NUM, &abilitySlot);
    CalculateMonStats(selected);
    GetMonNickname(selected, gStringVar1);
    if (target == SPECIES_DELTA_BULBASAUR)
        VarSet(VAR_BULBASAUR_FIELD_NOTES, BulbasaurNotes_GetUnlocks() | BULBASAUR_NOTES_DELTA_CONVERTED);
    return TRUE;
}
