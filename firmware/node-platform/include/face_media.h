#pragma once
#include <cstdint>
#include "cJSON.h"
const uint8_t* face_media_frame(unsigned index);
void face_media_load_sd(); // Storage worker only, holding the storage ownership gate.
void face_media_json(cJSON* root);
bool face_media_cached();
