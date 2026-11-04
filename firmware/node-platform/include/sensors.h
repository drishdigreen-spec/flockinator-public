#pragma once
#include "driver/i2c_master.h"
#include "cJSON.h"
struct Sensors {
    bool bus_ok=false, sht_ok=false, imu_ok=false, rtc_ok=false;
    bool rtc_advancing=false, rtc_valid=false;
    float temperature=0, humidity=0, ax=0, ay=0, az=0, gx=0, gy=0, gz=0;
    uint32_t observed_ms=0, imu_timestamp=0;
    uint8_t whoami=0, rtc_seconds=0, rtc_control=0;
    esp_err_t sht_error=ESP_ERR_INVALID_STATE, imu_error=ESP_ERR_INVALID_STATE, rtc_error=ESP_ERR_INVALID_STATE;
};
extern Sensors sensors;
void sensors_init();
void sensors_poll();
void sensors_json(cJSON* root);
i2c_master_bus_handle_t sensor_bus();
