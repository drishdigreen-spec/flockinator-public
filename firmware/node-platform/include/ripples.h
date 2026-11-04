#pragma once
#include "pixel_ui.h"
#include "cJSON.h"
void ripples_tick(const char* label);
void ripples_draw(node::Frame& frame,uint32_t now);
void ripples_json(cJSON* root);
