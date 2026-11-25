#include "global.h"
#include "berry_fix_program.h"
#include "clear_save_data_menu.h"
#include "decompress.h"
#include "event_data.h"
#include "gpu_regs.h"
#include "m4a.h"
#include "main.h"
#include "main_menu.h"
#include "palette.h"
#include "reset_rtc_screen.h"
#include "scanline_effect.h"
#include "sound.h"
#include "title_screen.h"
#include "constants/rgb.h"
#include "constants/songs.h"

#define CLEAR_SAVE_BUTTON_COMBO (B_BUTTON | SELECT_BUTTON | DPAD_UP)
#define RESET_RTC_BUTTON_COMBO (B_BUTTON | SELECT_BUTTON | DPAD_LEFT)
#define BERRY_UPDATE_BUTTON_COMBO (B_BUTTON | SELECT_BUTTON)
#define SCREEN_BLOCK 31
#define TILES_WIDE (DISPLAY_WIDTH / 8)
#define TILES_HIGH (DISPLAY_HEIGHT / 8)

static const u32 sReedwakeTitleGfx[] = INCGFX_U32("graphics/title_screen/reedwake.png", ".8bpp.lz");
static const u16 sReedwakeTitlePalette[] = INCGFX_U16("graphics/title_screen/reedwake.png", ".gbapal");

/* Intro blend table */

static void CB2_GoToMainMenu(void)
{
    if (!UpdatePaletteFade())
        SetMainCallback2(CB2_InitMainMenu);
}

static void CB2_GoToResetRtcScreen(void)
{
    if (!UpdatePaletteFade())
        SetMainCallback2(CB2_InitResetRtcScreen);
}

static void CB2_GoToBerryFixScreen(void)
{
    if (!UpdatePaletteFade())
    {
        m4aMPlayAllStop();
        SetMainCallback2(CB2_InitBerryFixProgram);
    }
}

static void VBlankCB(void)
{
    TransferPlttBuffer();
}

static void CB2_ReedwakeTitle(void)
{
    if (UpdatePaletteFade())
        return;
    if (JOY_NEW(A_BUTTON | START_BUTTON))
    {
        FadeOutBGM(4);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        SetMainCallback2(CB2_GoToMainMenu);
    }
    else if (JOY_HELD(CLEAR_SAVE_BUTTON_COMBO) == CLEAR_SAVE_BUTTON_COMBO)
    {
        SetMainCallback2(CB2_InitClearSaveDataScreen);
    }
    else if (JOY_HELD(RESET_RTC_BUTTON_COMBO) == RESET_RTC_BUTTON_COMBO && CanResetRTC())
    {
        FadeOutBGM(4);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        SetMainCallback2(CB2_GoToResetRtcScreen);
    }
    else if (JOY_HELD(BERRY_UPDATE_BUTTON_COMBO) == BERRY_UPDATE_BUTTON_COMBO)
    {
        FadeOutBGM(4);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        SetMainCallback2(CB2_GoToBerryFixScreen);
    }
}

void CB2_InitTitleScreen(void)
{
    u16 x, y;
    volatile u16 *tilemap = (volatile u16 *)BG_SCREEN_ADDR(SCREEN_BLOCK);

    SetVBlankCallback(NULL);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_FORCED_BLANK);
    ScanlineEffect_Stop();
    SetGpuReg(REG_OFFSET_BLDCNT, 0);
    SetGpuReg(REG_OFFSET_BLDALPHA, 0);
    SetGpuReg(REG_OFFSET_BLDY, 0);
    SetGpuReg(REG_OFFSET_BG0HOFS, 0);
    SetGpuReg(REG_OFFSET_BG0VOFS, 0);
    DmaFill16(3, 0, (void *)VRAM, VRAM_SIZE);
    ResetPaletteFade();

    LZ77UnCompVram(sReedwakeTitleGfx, (void *)BG_CHAR_ADDR(0));
    for (y = 0; y < TILES_HIGH; y++)
    {
        for (x = 0; x < TILES_WIDE; x++)
            tilemap[y * 32 + x] = y * TILES_WIDE + x;
    }
    LoadPalette(sReedwakeTitlePalette, 0, sizeof(sReedwakeTitlePalette));
    SetGpuReg(REG_OFFSET_BG0CNT, BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(SCREEN_BLOCK) | BGCNT_256COLOR | BGCNT_TXT256x256);
    BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
    SetVBlankCallback(VBlankCB);
    EnableInterrupts(INTR_FLAG_VBLANK);
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_MODE_0 | DISPCNT_BG0_ON);
    m4aSongNumStart(MUS_TITLE);
    SetMainCallback2(CB2_ReedwakeTitle);
}
