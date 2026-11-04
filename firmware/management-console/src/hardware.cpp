#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>
#include <TouchDrvGT911.hpp>
#include <driver/rtc_io.h>
#include <esp_heap_caps.h>
#include <esp_sleep.h>
#include "epd_driver.h"
#include "utilities.h"
#include "hardware.h"
#include "refresh_regions.h"
#include "touch_events.h"

namespace flockinator {
namespace {
Diagnostics state;
TouchDrvGT911 touch;
TouchGesture touch_gesture;
uint8_t* pixels = nullptr;
uint8_t* displayed_pixels = nullptr;
uint8_t* region_pixels = nullptr;
bool displayed_valid = false;
constexpr size_t kFramebufferBytes = kWidth * kHeight / 2;
void update_memory() {
    state.internal_free = heap_caps_get_free_size(MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
    state.psram_free = ESP.getFreePsram();
}
}

Diagnostics& diagnostics() { update_memory(); return state; }
uint8_t* screen_buffer() { return pixels; }

void hardware_begin() {
    Serial.setRxBufferSize(4096);
    Serial.setTxBufferSize(kSerialTxBytes);
    Serial.begin(115200); // Never wait for USB connection on a battery handheld.
    rtc_gpio_deinit(GPIO_NUM_21);
    pinMode(BUTTON_1, INPUT_PULLUP);
    update_memory();
    if (psramFound() && state.internal_free >= 160000) {
        pixels = static_cast<uint8_t*>(heap_caps_calloc(kFramebufferBytes, 1, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    }
    if (!pixels) {
        state.note = "Insufficient memory: display unavailable";
        Serial.printf("display=unavailable reason=memory\n");
        return;
    }
    memset(pixels, 0xFF, kFramebufferBytes);
    displayed_pixels = static_cast<uint8_t*>(heap_caps_malloc(kFramebufferBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    region_pixels = static_cast<uint8_t*>(heap_caps_malloc(kFramebufferBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
    if (!displayed_pixels || !region_pixels) {
        heap_caps_free(displayed_pixels); heap_caps_free(region_pixels);
        displayed_pixels = region_pixels = nullptr;
        Serial.printf("display:regional_unavailable fallback=full\n");
    }
    epd_init(); // Vendor API has no panel-presence result. Called exactly once.
    state.display_buffer = true;
    if (esp_sleep_get_wakeup_cause() != ESP_SLEEP_WAKEUP_UNDEFINED) delay(1000);

    Wire.begin(BOARD_SDA, BOARD_SCL);
    Wire.setTimeOut(50);
    pinMode(TOUCH_INT, OUTPUT);
    digitalWrite(TOUCH_INT, HIGH);
    delay(8);
    for (uint8_t address : {uint8_t(0x14), uint8_t(0x5D)}) {
        Wire.beginTransmission(address);
        if (Wire.endTransmission() == 0) { state.touch_address = address; break; }
    }
    if (state.touch_address) {
        touch.setPins(-1, TOUCH_INT);
        state.touch = touch.begin(Wire, state.touch_address, BOARD_SDA, BOARD_SCL);
        touch.setSwapXY(false);
        touch.setMirrorXY(false, false);
    }
    pinMode(TOUCH_INT, INPUT);

    SPI.begin(SD_SCLK, SD_MISO, SD_MOSI, SD_CS);
    state.sd = SD.begin(SD_CS, SPI, 4000000, "/sd", 5, false);
    if (state.sd) {
        const uint8_t type = SD.cardType();
        state.sd = type != CARD_NONE;
        state.sd_type = type == CARD_SDHC ? "SDHC/SDXC" : type == CARD_SD ? "SDSC" : type == CARD_MMC ? "MMC" : "unknown";
        state.sd_capacity_mb = static_cast<uint32_t>(SD.cardSize() / (1024 * 1024));
    }
    state.note = state.touch ? "Panel image needs visual verification" : "Touch unavailable; button cycles pages";
    print_diagnostics();
}

void print_diagnostics() {
    update_memory();
    Serial.printf("build=%s display_buffer=%d touch=%d sd_mount=%d sd_mib=%lu internal=%lu psram=%lu\n",
        kVersion, state.display_buffer, state.touch, state.sd,
        static_cast<unsigned long>(state.sd_capacity_mb), static_cast<unsigned long>(state.internal_free),
        static_cast<unsigned long>(state.psram_free));
}

bool read_touch(Point& point) {
    if (!state.touch) return false;
    // Read a fresh GT911 report, then acknowledge it AFTER copying coordinates.
    // SensorLib 0.3.1 getPoint ignores readiness and acknowledges before reading.
    auto read_register = [](uint16_t reg, uint8_t* data, uint8_t length) {
        Wire.beginTransmission(state.touch_address);
        Wire.write(uint8_t(reg >> 8)); Wire.write(uint8_t(reg));
        if (Wire.endTransmission(false) != 0) return false;
        if (Wire.requestFrom(state.touch_address, length) != length) return false;
        for (uint8_t i=0;i<length;++i) data[i]=Wire.read();
        return true;
    };
    uint8_t status=0, report[8]{};
    if (!read_register(0x814e,&status,1) || !(status & 0x80)) return false;
    const uint8_t count=status & 0x0f;
    if (count==1 && !read_register(0x814f,report,sizeof(report))) return false;
    Wire.beginTransmission(state.touch_address);
    Wire.write(uint8_t(0x81)); Wire.write(uint8_t(0x4e)); Wire.write(uint8_t(0));
    if (Wire.endTransmission() != 0) return false;
    point=count==1 ? landscape_touch(report[1] | (uint16_t(report[2])<<8),
                                    report[3] | (uint16_t(report[4])<<8)) : Point{-1,-1};
    const bool tapped=touch_gesture.accept(true,count!=0,point);
    if (tapped) Serial.printf("touch:tap x=%d y=%d\n",point.x,point.y);
    return tapped;
}

bool button_down() { return digitalRead(BUTTON_1) == LOW; }

bool refresh_screen(bool full) {
    if (!pixels) return false;
    full = full || !displayed_valid || !displayed_pixels || !region_pixels;
    const Rect region = full ? Rect{0,0,kWidth,kHeight} : changed_region(displayed_pixels,pixels);
    if (!region.w || !region.h) return false;
    const Rect_t area{region.x,region.y,region.w,region.h};
    if (!full) pack_region(pixels,region,region_pixels);
    const uint32_t started = millis();
    Serial.printf("refresh:region mode=%s x=%d y=%d w=%d h=%d\n",full?"full":"regional",region.x,region.y,region.w,region.h);
    Serial.printf("refresh:poweron heap=%u largest=%u dma=%u\n",(unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT),(unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT),(unsigned)heap_caps_get_free_size(MALLOC_CAP_DMA));
    epd_poweron();
    Serial.printf("refresh:clear\n");
    epd_clear_area(area);
    Serial.printf("refresh:draw heap=%u largest=%u\n",(unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT),(unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT));
    epd_draw_grayscale_image(area, full ? pixels : region_pixels);
    Serial.printf("refresh:poweroff\n");
    epd_poweroff();
    Serial.printf("refresh:done\n");
    state.refresh_ms = millis() - started;
    ++state.redraws;
    if (displayed_pixels) memcpy(displayed_pixels,pixels,kFramebufferBytes);
    displayed_valid = true;
    Serial.printf("refresh:timing mode=%s duration_ms=%lu count=%lu\n",full?"full":"regional",(unsigned long)state.refresh_ms,(unsigned long)state.redraws);
    update_memory();
    return true;
}

bool enter_sleep() {
    const uint32_t started = millis();
    while (button_down()) {
        if (static_cast<uint32_t>(millis() - started) >= 3000) {
            state.note = "Sleep cancelled: release the button";
            return false;
        }
        delay(10);
    }
    if (esp_sleep_enable_ext1_wakeup(1ULL << 21, ESP_EXT1_WAKEUP_ANY_LOW) != ESP_OK) {
        state.note = "Sleep wake configuration failed";
        return false;
    }
    if (rtc_gpio_pullup_en(GPIO_NUM_21) != ESP_OK ||
        rtc_gpio_pulldown_dis(GPIO_NUM_21) != ESP_OK ||
        esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON) != ESP_OK) {
        rtc_gpio_deinit(GPIO_NUM_21);
        pinMode(BUTTON_1, INPUT_PULLUP);
        state.note = "Sleep cancelled: RTC setup failed";
        return false;
    }
    SD.end();
    SPI.end();
    if (state.touch) touch.sleep();
    delay(5);
    Wire.end();
    pinMode(BOARD_SDA, OPEN_DRAIN);
    pinMode(BOARD_SCL, OPEN_DRAIN);
    pinMode(TOUCH_INT, OPEN_DRAIN);
    epd_poweroff_all();
    Serial.flush();
    esp_deep_sleep_start();
    return true; // Not reached after successful sleep.
}
} // namespace flockinator
