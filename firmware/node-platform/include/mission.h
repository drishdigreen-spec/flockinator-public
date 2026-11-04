#pragma once
#include "../../shared/recon/model.h"
#include "cJSON.h"
void mission_init(const char *label);
recon::Runtime mission_snapshot();
bool mission_apply(const recon::Config &, bool start, uint32_t delay);
const char *mission_command(cJSON *);
void mission_json(cJSON *);
void mission_health(uint8_t *payload);
