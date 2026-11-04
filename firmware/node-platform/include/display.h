#pragma once
#include "cJSON.h"
bool display_init();
void display_tick(const char* label,bool memory_ok);
void display_json(cJSON* root);
void display_next_page();

const char* display_command(cJSON* request);
