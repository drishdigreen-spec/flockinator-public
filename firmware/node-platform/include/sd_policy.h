#pragma once
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdio>
namespace node {
struct SdIdentity {
    uint32_t manufacturer=0,oem=0,revision=0,date=0,serial=0;
    uint64_t bytes=0;
    uint32_t sector=0;
    uint8_t name[8]{};
};
inline bool same_card(const SdIdentity& a,const SdIdentity& b) {
    return a.manufacturer==b.manufacturer && a.oem==b.oem && a.revision==b.revision &&
        a.date==b.date && a.serial==b.serial && a.bytes==b.bytes && a.sector==b.sector && !memcmp(a.name,b.name,8);
}
inline bool sd_supported(const SdIdentity& a) {
    return a.sector==512 && a.bytes>=4ULL*1024*1024*1024 && a.bytes<=128ULL*1024*1024*1024 && !(a.bytes%512);
}
inline void sd_identity_text(const SdIdentity& a,char* out,size_t length) {
    char name[17]{};
    for(unsigned i=0;i<8;++i) snprintf(name+2*i,3,"%02x",a.name[i]);
    snprintf(out,length,"%08lx%08lx%08lx%08lx%08lx%016llx%08lx%s",
        (unsigned long)a.manufacturer,(unsigned long)a.oem,(unsigned long)a.revision,
        (unsigned long)a.date,(unsigned long)a.serial,(unsigned long long)a.bytes,(unsigned long)a.sector,name);
}
struct SdPermit {
    SdIdentity card{}; char token[33]{}; uint64_t expires=0; bool valid=false;
    void prepare(const SdIdentity& id,const char* value,uint64_t now) {
        valid=false;
        if(!sd_supported(id) || !value || strlen(value)!=32) return;
        card=id; memcpy(token,value,33); expires=now+120000; valid=true;
    }
    bool consume(const SdIdentity& current,const char* value,uint64_t now) {
        bool accepted=valid && now<expires && same_card(card,current) && value && !strcmp(token,value);
        valid=false; return accepted;
    }
};
// SplitMix64: deterministic, address-dependent test data, not a cryptographic key.
inline uint64_t sd_pattern(uint64_t word_address,uint64_t seed) {
    uint64_t z=word_address+seed+0x9e3779b97f4a7c15ULL;
    z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
    z=(z^(z>>27))*0x94d049bb133111ebULL;
    return z^(z>>31);
}
}
