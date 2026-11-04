#pragma once
#include <cstdint>
#include <cstddef>
#include "cJSON.h"
void node_link_init();
bool node_link_ready();
void node_link_receive(const uint8_t source[6], const uint8_t* data, size_t length);
void node_link_publish(cJSON* status);
void node_link_json(cJSON* status);
