#pragma once
#include "controller_json.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
struct Guard {SemaphoreHandle_t h;explicit Guard(SemaphoreHandle_t s):h(s){xSemaphoreTake(h,portMAX_DELAY);}~Guard(){xSemaphoreGive(h);}};
bool fleet_init(nvs_handle_t store);
bool fleet_provision(const char* line);
Json fleet_snapshot();
bool fleet_command(const Json& cmd,string& error);
bool signed_panel(int i,const char* method,const char* path,const string& body,string& reply);
void deliver_next(int i);
void archive_tick();
string sha256hex(const string& bytes);
