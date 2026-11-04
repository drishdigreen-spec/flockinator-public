#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include "../../shared/commissioning/wire.h"

namespace node {
constexpr uint32_t LinkTimeoutMs=20000;
inline bool valid_manifest(const uint8_t* body,size_t length,uint32_t slot_size) {
    if(!body || length!=73 || memcmp(body+68,"WS32",4) || body[72]!=1) return false;
    uint32_t image_size=flockwire::get32(body);
    return image_size>=288 && image_size<=slot_size;
}
inline bool valid_first_chunk(const uint8_t* bytes,size_t length) {
    // ESP image header: magic at zero; chip ID at byte 12 (ESP32-S3 = 9).
    return bytes && length>=24 && bytes[0]==0xe9 && flockwire::get16(bytes+12)==9;
}
inline bool link_expired(uint32_t now,uint32_t touched) {
    return uint32_t(now-touched)>=LinkTimeoutMs;
}
}
