#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
namespace flockinator {
inline bool reply_timed_out(bool beginning,uint32_t now,uint32_t started) {
    return now-started >= (beginning ? 60000U : 4000U);
}

inline bool valid_image_name(const char* name) {
    if(!name || !name[0] || name[0]=='.' || std::strlen(name)>64)return false;
    for(const char* p=name;*p;++p) {
        const char c=*p;
        if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='-'||c=='_'||c=='.'))return false;
    }
    return true;
}
inline bool may_select_image(bool mounted, bool busy, bool uploading, const char* name) {
    return mounted && !busy && !uploading && valid_image_name(name);
}
inline bool health_retry_due(bool pending, uint8_t retries, uint32_t now,
                             uint32_t requested_at, uint32_t attempted_at) {
    return pending && retries < 2 && now-requested_at < 1800 && now-attempted_at >= 500;
}
inline bool expected_health(bool pending, uint32_t now, uint32_t requested_at,
                            uint32_t sequence, uint32_t expected_sequence,
                            const uint8_t* nonce, const uint8_t* expected_nonce) {
    return pending && now-requested_at<=4000 && sequence==expected_sequence &&
           std::memcmp(nonce,expected_nonce,16)==0;
}
inline bool valid_deployment_boot(uint32_t previous_boots,uint32_t boots,uint8_t ota,
                                 uint8_t receiver,bool core,const uint8_t* image,const uint8_t* expected) {
    return boots!=previous_boots && ota==2 && receiver==1 && core && std::memcmp(image,expected,32)==0;
}
}
