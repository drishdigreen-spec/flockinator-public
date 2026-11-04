// Pin map and QMI setup referenced from Waveshare ESP32-S3-RGB-Matrix, commit4047e4.
#include "sensors.h"
#include "node_model.h"
#include "qmi8658.h"
#include "esp_timer.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <cmath>
Sensors sensors;
static i2c_master_bus_handle_t bus;
static i2c_master_dev_handle_t sht,rtc;
static qmi8658_dev_t imu{};
static bool imu_ready=false, had_rtc=false;
static uint8_t previous_seconds=0;
i2c_master_bus_handle_t sensor_bus() { return bus; }
static esp_err_t add(uint8_t address,i2c_master_dev_handle_t* handle) {
    i2c_device_config_t c{}; c.dev_addr_length=I2C_ADDR_BIT_LEN_7;
    c.device_address=address; c.scl_speed_hz=100000;
    return i2c_master_bus_add_device(bus,&c,handle);
}
static esp_err_t sht_command(uint16_t command) {
    uint8_t bytes[]={static_cast<uint8_t>(command>>8),static_cast<uint8_t>(command)};
    return i2c_master_transmit(sht,bytes,2,100);
}
void sensors_init() {
    i2c_master_bus_config_t c{}; c.i2c_port=I2C_NUM_0; c.sda_io_num=GPIO_NUM_47;
    c.scl_io_num=GPIO_NUM_48; c.clk_source=I2C_CLK_SRC_DEFAULT;
    c.glitch_ignore_cnt=7; c.flags.enable_internal_pullup=true;
    sensors.bus_ok=i2c_new_master_bus(&c,&bus)==ESP_OK;
    if(!sensors.bus_ok) return;
    add(0x70,&sht); add(0x51,&rtc);
    sensors.imu_error=qmi8658_init(&imu,bus,QMI8658_ADDRESS_HIGH);
    imu_ready=sensors.imu_error==ESP_OK;
    if(imu_ready) { qmi8658_get_who_am_i(&imu,&sensors.whoami); qmi8658_set_accel_unit_mps2(&imu,true); }
}
void sensors_poll() {
    if(!sensors.bus_ok) return;
    if(sht) {
        uint8_t raw[6]{};
        esp_err_t e=sht_command(0x3517); esp_rom_delay_us(500); // SHTC3 wake needs >=240 us; 2 ms rounded to zero at 100 Hz.
        if(e==ESP_OK) e=sht_command(0x7866);
        vTaskDelay(pdMS_TO_TICKS(20));
        if(e==ESP_OK) e=i2c_master_receive(sht,raw,6,100);
        if(e==ESP_OK && (node::crc8(raw,2)!=raw[2] || node::crc8(raw+3,2)!=raw[5])) e=ESP_ERR_INVALID_CRC;
        auto sleep=sht_command(0xB098); if(e==ESP_OK) e=sleep;
        sensors.sht_error=e; sensors.sht_ok=e==ESP_OK;
        if(sensors.sht_ok) { sensors.temperature=-45+175.0f*((raw[0]<<8)|raw[1])/65536;
            sensors.humidity=100.0f*((raw[3]<<8)|raw[4])/65536; }
    }
    if(imu_ready) {
        qmi8658_data_t d{}; bool ready=false;
        esp_err_t e=qmi8658_is_data_ready(&imu,&ready);
        if(e==ESP_OK && ready) e=qmi8658_read_sensor_data(&imu,&d);
        sensors.imu_ok=e==ESP_OK && ready && std::isfinite(d.accelX) && std::isfinite(d.accelY) && std::isfinite(d.accelZ) && std::isfinite(d.gyroX) && std::isfinite(d.gyroY) && std::isfinite(d.gyroZ) && d.timestamp!=sensors.imu_timestamp;
        sensors.imu_error=e; if(sensors.imu_ok) { sensors.ax=d.accelX; sensors.ay=d.accelY; sensors.az=d.accelZ; sensors.gx=d.gyroX; sensors.gy=d.gyroY; sensors.gz=d.gyroZ; sensors.imu_timestamp=d.timestamp; }
    }
    if(rtc) {
        uint8_t reg=0,raw[11]{};
        sensors.rtc_error=i2c_master_transmit_receive(rtc,&reg,1,raw,sizeof(raw),100);
        sensors.rtc_ok=sensors.rtc_error==ESP_OK;
        if(sensors.rtc_ok) {
            sensors.rtc_control=raw[0]; sensors.rtc_seconds=raw[4];
            sensors.rtc_advancing=had_rtc && (raw[4]&0x7f)!=previous_seconds && !(raw[0]&0x20);
            sensors.rtc_valid=!(raw[4]&0x80) && !(raw[0]&0x20) && (raw[4]&0x7f)<=0x59 && (raw[4]&15)<=9;
            previous_seconds=raw[4]&0x7f; had_rtc=true;
        }
    }
    sensors.observed_ms=esp_timer_get_time()/1000;
}
void sensors_json(cJSON* root) {
    auto* j=cJSON_AddObjectToObject(root,"sensors");
    cJSON_AddNumberToObject(j,"observed_at_ms",sensors.observed_ms);
    cJSON_AddStringToObject(j,"shtc3",sensors.sht_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"shtc3_error",esp_err_to_name(sensors.sht_error));
    if(sensors.sht_ok) { cJSON_AddNumberToObject(j,"temperature_c",sensors.temperature); cJSON_AddNumberToObject(j,"humidity_percent",sensors.humidity); }
    cJSON_AddStringToObject(j,"qmi8658",sensors.imu_ok?"PASS":"PENDING");
    cJSON_AddNumberToObject(j,"qmi_whoami",sensors.whoami);
    cJSON_AddStringToObject(j,"qmi_error",esp_err_to_name(sensors.imu_error));
    cJSON_AddNumberToObject(j,"qmi_timestamp",sensors.imu_timestamp);
    if(sensors.imu_ok) { double a[]={sensors.ax,sensors.ay,sensors.az}; cJSON_AddItemToObject(j,"accel_m_s2",cJSON_CreateDoubleArray(a,3)); double g[]={sensors.gx,sensors.gy,sensors.gz}; cJSON_AddItemToObject(j,"gyro_deg_s",cJSON_CreateDoubleArray(g,3)); }
    cJSON_AddStringToObject(j,"rtc_bus",sensors.rtc_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"rtc_clock",sensors.rtc_advancing?"PASS":"PENDING");
    cJSON_AddStringToObject(j,"rtc_time",sensors.rtc_valid?"UNVERIFIED":"TIME_UNSET");
    cJSON_AddNumberToObject(j,"rtc_seconds_raw",sensors.rtc_seconds);
    cJSON_AddNumberToObject(j,"rtc_control_raw",sensors.rtc_control);
}
