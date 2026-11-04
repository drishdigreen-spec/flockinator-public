#pragma once
#include "console_model.h"

namespace flockinator {
struct Diagnostics {
    bool display_buffer = false;
    bool touch = false;
    bool sd = false;
    uint8_t touch_address = 0;
    uint32_t internal_free = 0;
    uint32_t psram_free = 0;
    uint32_t refresh_ms = 0;
    uint32_t redraws = 0;
    uint32_t sd_capacity_mb = 0;
    const char* sd_type = "unknown";
    const char* note = "Hardware checks pending";
};

void hardware_begin();
Diagnostics& diagnostics();
uint8_t* screen_buffer();
bool read_touch(Point& point);
bool button_down();
bool refresh_screen(bool full);
void print_diagnostics();
bool enter_sleep();
} // namespace flockinator
