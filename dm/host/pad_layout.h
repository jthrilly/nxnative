// Face buttons of a physical controller (front_mac.m, DmGamepad.m; pure, so tests/t_hid.c checks it without controllers). DM_FACE_BUTTONS=label (the default) maps every
// controller's buttons name for name, so an Xbox or PlayStation controller's A is the Switch's A as the game's prompts show it. GameController names a Nintendo controller's
// buttons by their printed labels too, so it maps the same either way. position keeps the Switch's places on other controllers (Xbox B is A, Xbox A is B, Y and X the same):
// pad_apple.h dm_pad_face.
#pragma once
#include <string.h>

// 1: every controller's buttonA is the Switch's A (by label); 0: dm_pad_face (by position, a Nintendo controller by its labels). mode: DM_FACE_BUTTONS (NULL: unset)
static int pad_by_label(const char *mode) { return !(mode && !strcmp(mode, "position")); }
