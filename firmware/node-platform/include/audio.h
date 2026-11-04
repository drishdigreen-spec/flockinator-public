#pragma once
#include "cJSON.h"
void audio_init();
void audio_poll();
bool audio_tone();
void audio_json(cJSON* root);
bool audio_ready();
double audio_level(int channel);
