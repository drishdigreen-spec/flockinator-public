#pragma once
#include "cJSON.h"
#include <cstdint>
void maintenance_init(const char* mac);
bool maintenance_set_key(const char* hex);
void maintenance_json(cJSON* root);
void maintenance_publish(cJSON* status);
void maintenance_tick();
bool maintenance_busy();
bool maintenance_ready();
bool maintenance_copy_key(uint8_t out[32]);
bool maintenance_claim_update();
void maintenance_release_update();
bool maintenance_claim_storage();
void maintenance_release_storage();
bool maintenance_storage_busy();
