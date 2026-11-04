#pragma once
#include "cJSON.h"
#include <cstdint>
#include <cstddef>
void network_init();
void network_tick(const char* label);
void network_json(cJSON* root);
bool network_configure(const char* ssid,const char* password);
bool network_connected();
bool network_now_ready();
bool network_peer_recent();
uint8_t network_channel();
void network_ip(char* buffer,size_t length);
