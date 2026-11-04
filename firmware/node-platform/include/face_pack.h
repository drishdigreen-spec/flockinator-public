#pragma once
#include <cstdint>
#include <cstddef>
#include <cstring>
namespace node {
inline uint32_t face_u32(const uint8_t* p){return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);}
inline bool valid_face_pack(const uint8_t* p,size_t n){
 if(!p || n<16 || std::memcmp(p,"FLKFACE1",8))return false;
 uint32_t count=face_u32(p+8);return count>=1&&count<=64&&face_u32(p+12)==8192&&n==16+size_t(count)*8192;
}
}
