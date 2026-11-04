#include "../crypto.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

using namespace flockwire;
static unsigned checks=0;
static void require(bool result,const char* description) {
    ++checks;
    if(!result) { std::fprintf(stderr,"FAIL: %s\n",description); std::exit(1); }
}
static void from_hex(const char* text,uint8_t* bytes,size_t size) {
    for(size_t i=0;i<size;++i) {
        unsigned value=0;
        if(std::sscanf(text+2*i,"%2x",&value)!=1) std::abort();
        bytes[i]=static_cast<uint8_t>(value);
    }
}
static Frame fixture(const uint8_t key[32]) {
    const uint8_t sender[6]={0x38,0x44,0xbe,0xcc,0x6e,0x4c};
    const uint8_t target[6]={0x94,0xa9,0x90,0xe5,0x16,0x38};
    uint8_t nonce[16]; for(size_t i=0;i<sizeof(nonce);++i) nonce[i]=i;
    const uint8_t payload[8]={0,0,0,0,0xe9,9,0,0xff};
    Frame frame;
    require(encode(frame,Kind::Data,sender,target,nonce,0x12345678,payload,sizeof(payload)),"encode golden fixture");
    require(sign(frame,key),"production sign golden fixture");
    return frame;
}
static void known_hmac_vector() {
    // RFC 4231 test case 1; this also checks that the portable dependency is real HMAC-SHA256.
    uint8_t key[20]; std::memset(key,0x0b,sizeof(key));
    const uint8_t message[]={'H','i',' ','T','h','e','r','e'};
    uint8_t expected[32],actual[32];
    from_hex("b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7",expected,32);
    require(mbedtls_md_hmac(mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),key,sizeof(key),message,sizeof(message),actual)==0,"RFC 4231 HMAC runs");
    require(equal(expected,actual,32),"RFC 4231 HMAC matches published vector");
}
static void production_frame_authentication() {
    uint8_t key[32]; for(size_t i=0;i<sizeof(key);++i) key[i]=i;
    Frame original=fixture(key);
    uint8_t expected[32];
    // Independently calculated with Python stdlib hmac over the explicit wire bytes.
    from_hex("9b0ac06ef8deb89ced67578610bad7aff0476be84e04eec12af4daceb76af13c",expected,32);
    require(equal(expected,original.bytes+original.size-Tag,32),"production sign matches fixed wire HMAC vector");
    View view{};
    require(authenticate(original.bytes,original.size,key,view),"fresh valid production frame authenticates");
    require(view.sequence==0x12345678 && view.length==8 && view.kind==Kind::Data,"authenticated view preserves exact fields");

    // Flip each individual byte: structural checks or HMAC must reject every mutation.
    // This includes both identities, nonce, sequence, payload, and all 32 tag bytes.
    for(size_t i=0;i<original.size;++i) {
        Frame changed=original; changed.bytes[i]^=1;
        require(!authenticate(changed.bytes,changed.size,key,view),"single-byte header/payload/tag mutation rejected");
    }
    uint8_t wrong_key[32]; std::memcpy(wrong_key,key,32); wrong_key[31]^=1;
    require(!authenticate(original.bytes,original.size,wrong_key,view),"wrong key rejected");
    for(size_t length=0;length<original.size;++length)
        require(!authenticate(original.bytes,length,key,view),"every truncated frame rejected");
    Frame appended=original; appended.bytes[appended.size++]=0;
    require(!authenticate(appended.bytes,appended.size,key,view),"trailing byte rejected");
    require(!authenticate(nullptr,original.size,key,view),"null frame rejected");
    require(authenticate(original.bytes,original.size,key,view),"valid frame still authenticates after rejection cases");

    Frame fresh=original; fresh.bytes[20]^=0x80;
    require(sign(fresh,key),"changed challenge is signed afresh");
    require(authenticate(fresh.bytes,fresh.size,key,view),"new signed challenge authenticates");
    require(!equal(fresh.bytes+fresh.size-Tag,original.bytes+original.size-Tag,32),"fresh challenge changes HMAC");
}
int main() {
    known_hmac_vector(); production_frame_authentication();
    std::printf("PASS: %u production crypto checks (real portable Mbed TLS)\n",checks);
}
