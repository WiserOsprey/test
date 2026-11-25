/* Exercise the built ROM's title renderer and transition with mGBA. */
#include <mgba/core/core.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 160
#define TITLE_WAIT_FRAMES 2400
#define MENU_WAIT_FRAMES 240
#define START_KEY (1u << 3)

static color_t sPixels[SCREEN_WIDTH * SCREEN_HEIGHT];

static bool WaitForCallback(struct mCore *core, uint32_t callbackPtr, uint32_t target, unsigned frames)
{
    for (unsigned frame = 0; frame < frames; frame++)
    {
        core->runFrame(core);
        if ((core->busRead32(core, callbackPtr) & ~1u) == (target & ~1u))
            return true;
    }
    return false;
}

static unsigned TitleColorCount(void)
{
    color_t seen[32];
    unsigned n = 0;
    for (unsigned y = 0; y < SCREEN_HEIGHT; y += 4)
    {
        for (unsigned x = 0; x < SCREEN_WIDTH; x += 4)
        {
            color_t color = sPixels[y * SCREEN_WIDTH + x];
            unsigned k = 0;
            while (k < n && seen[k] != color)
                k++;
            if (k == n)
            {
                seen[n++] = color;
                if (n == sizeof(seen) / sizeof(seen[0]))
                    return n;
            }
        }
    }
    return n;
}

int main(int argc, char **argv)
{
    if (argc != 5)
    {
        fputs("usage: smoke ROM gMain title_cb menu_cb\n", stderr);
        return 1;
    }
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
    {
        fputs("mGBA couldn't initialize the ROM\n", stderr);
        return 1;
    }

    int result = 1;
    mCoreInitConfig(core, NULL);
    core->setVideoBuffer(core, sPixels, SCREEN_WIDTH);
    if (!mCoreLoadFile(core, argv[1]))
    {
        fputs("mGBA couldn't load the ROM\n", stderr);
        goto cleanup;
    }
    core->reset(core);

    // gMain holds the frame callback immediately after the first callback.
    uint32_t callbackPtr = (uint32_t)strtoul(argv[2], NULL, 16) + 4;
    uint32_t title = (uint32_t)strtoul(argv[3], NULL, 16);
    uint32_t menu = (uint32_t)strtoul(argv[4], NULL, 16);
    if (!WaitForCallback(core, callbackPtr, title, TITLE_WAIT_FRAMES))
    {
        fputs("The game didn't reach Reedwake's title screen\n", stderr);
        goto cleanup;
    }
    for (unsigned i = 0; i < 45; i++)
        core->runFrame(core);
    unsigned colors = TitleColorCount();
    if (colors < 16)
    {
        fprintf(stderr, "Title screen rendered only %u colors\n", colors);
        goto cleanup;
    }

    core->setKeys(core, START_KEY);
    core->runFrame(core);
    core->runFrame(core);
    core->setKeys(core, 0);
    if (!WaitForCallback(core, callbackPtr, menu, MENU_WAIT_FRAMES))
    {
        fputs("Start didn't open the main menu\n", stderr);
        goto cleanup;
    }
    printf("mGBA rendered the Reedwake title (%u+ colors) and Start opened the main menu.\n", colors);
    result = 0;

cleanup:
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return result;
}
