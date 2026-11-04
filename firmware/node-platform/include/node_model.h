#pragma once
#include <cstddef>
#include <cstring>
#include <cstdint>
namespace node {
inline bool valid_label(const char* s) { return s && std::strlen(s)==2 && s[0]>='A' && s[0]<='D' && s[1]>='1' && s[1]<='4'; }
inline uint8_t brightness(int percent) { return static_cast<uint8_t>((percent<0?0:percent>50?50:percent)*255/100); }
inline uint8_t crc8(const uint8_t* data, size_t count) {
    uint8_t crc=0xff;
    for(size_t i=0;i<count;i++) {
        crc ^= data[i];
        for(int bit=0;bit<8;bit++) crc=(crc & 0x80)?(crc<<1)^0x31:crc<<1;
    }
    return crc;
}
class LineBuffer {
public:
    enum Result { More, Ready, Overflow };
    Result push(char c) {
        if (done_) { count_=0; done_=false; }
        if(c=='\r') return More;
        if(c=='\n') { done_=true; bytes_[count_]=0; bool was=overflow_; overflow_=false; return was?Overflow:Ready; }
        if(count_>=sizeof(bytes_)-1) overflow_=true;
        if(!overflow_) bytes_[count_++]=c;
        return More;
    }
    const char* data() const { return bytes_; }
private:
    char bytes_[1024]{};
    size_t count_=0;
    bool overflow_=false, done_=false;
};
}
