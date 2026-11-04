#pragma once
#include "wire.h"
#include "mbedtls/md.h"
namespace flockwire {
inline bool sign(Frame& frame,const uint8_t* key) {
    return frame.size>=Header+Tag && mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),key,32,frame.bytes,frame.size-Tag,frame.bytes+frame.size-Tag)==0;
}
inline bool authenticate(const uint8_t* bytes,size_t size,const uint8_t* key,View& view) {
    if(!decode(bytes,size,view))return false;
    uint8_t digest[32];
    return mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),key,32,bytes,size-Tag,digest)==0 && equal(digest,view.tag,32);
}
}
