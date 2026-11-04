#pragma once
#include <stdbool.h>
bool feedback_init(void);
void feedback_play(int volume, int frequency);
void feedback_event(int volume, int frequency, int state);
