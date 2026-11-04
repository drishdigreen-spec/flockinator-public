#pragma once
#include "cJSON.h"
#include <cstdint>
void storage_init();
void storage_json(cJSON* root);
const char* storage_state();
// 1: inspect/prepare, 2: explicit FAT32 reset + quick test, 3: reset + full test.
const char* storage_request(int op,const char* card_id,const char* token,uint32_t& job);
void storage_report(uint8_t* report,uint8_t code,uint32_t accepted_job=0);

void storage_seed_media();
