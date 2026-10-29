// Face buttons of a physical controller (front_mac.m, DmGamepad.m; pure, so tests/t_hid.c checks it without controllers). GameController names them by position (buttonA is the
// bottom one), and the Switch's A is the right one. DM_FACE_BUTTONS=label (the default) follows an Xbox or PlayStation controller's printed labels, so Xbox A is the Switch's A
// as the game's prompts show it; position keeps the Switch's places (Xbox B is A, Xbox A is B, Y and X the same). A Nintendo controller has the Switch's labels in the Switch's
// places, so it keeps the positions either way.
#pragma once
#include <string.h>

static int pad_nintendo(const char *category, const char *vendor) {
    static const char *const marks[] = {"Switch", "Joy-Con", "Nintendo"};
    for (unsigned i = 0; i < sizeof marks / sizeof *marks; i++)
        if ((category && strstr(category, marks[i])) || (vendor && strstr(vendor, marks[i]))) return 1;
    return 0;
}
// 1: the controller's buttonA is the Switch's A; 0: its buttonB is (by position). mode: DM_FACE_BUTTONS (NULL: unset)
static int pad_by_label(const char *mode, const char *category, const char *vendor) {
    if (mode && !strcmp(mode, "position")) return 0;
    return !pad_nintendo(category, vendor);
}
