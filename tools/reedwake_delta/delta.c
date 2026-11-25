#include "global.h"
#include "bulbasaur_field_notes.h"
#include "event_data.h"
#include "party_menu.h"
#include "pokemon.h"
#include "reedwake_delta.h"
#include "string_util.h"
#include "constants/species.h"
#include "constants/vars.h"

enum
{
    DELTA_UNSUPPORTED,
    DELTA_READY,
    DELTA_TRIAL_REQUIRED,
    DELTA_ALREADY_CONVERTED,
};

static const struct
{
    u16 standard;
    u16 delta;
} sDeltaForms[] =
{
    /* Delta mapping */
};

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
