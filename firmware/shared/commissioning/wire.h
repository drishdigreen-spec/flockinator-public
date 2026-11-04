#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
namespace flockwire {
constexpr size_t Header=40, Tag=32, MaxPayload=160, MaxFrame=232, HealthSize=96;
enum class Kind:uint8_t { Poll=1,Health=2,Open=3,Challenge=4,Begin=5,Data=6,Commit=7,Abort=8,Ack=9,SdRequest=10,SdReply=11,Mission=12,MissionReply=13 };
enum class Code:uint8_t { Ok=0,Busy=1,Invalid=2,Order=3,Storage=4,Digest=5,Unsupported=6 };
struct Frame { uint8_t bytes[MaxFrame]{}; size_t size=0; };
struct View { Kind kind; const uint8_t *sender,*target,*nonce,*payload,*tag; uint32_t sequence; uint16_t length; };
inline uint16_t get16(const uint8_t* p) {return uint16_t(p[0])|uint16_t(p[1])<<8;}
inline uint32_t get32(const uint8_t* p) {return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24;}
inline void put16(uint8_t* p,uint16_t v) {p[0]=v;p[1]=v>>8;}
inline void put32(uint8_t* p,uint32_t v) {for(int i=0;i<4;++i)p[i]=v>>(8*i);}
inline bool equal(const uint8_t* a,const uint8_t* b,size_t n) {uint8_t d=0;for(size_t i=0;i<n;++i)d|=a[i]^b[i];return d==0;}
inline bool decode(const uint8_t* bytes,size_t n,View& out) {
    if(!bytes || n<Header+Tag || n>MaxFrame || memcmp(bytes,"FLK2",4) || bytes[4]!=1 || bytes[5]<1 || bytes[5]>13)return false;
    auto len=get16(bytes+6);if(len>MaxPayload || n!=Header+Tag+len)return false;
    out={Kind(bytes[5]),bytes+8,bytes+14,bytes+20,bytes+Header,bytes+Header+len,get32(bytes+36),len};return true;
}
inline bool encode(Frame& f,Kind kind,const uint8_t* sender,const uint8_t* target,const uint8_t* nonce,uint32_t sequence,const uint8_t* body,size_t n) {
    if(n>MaxPayload || (n && !body))return false;
    f={};memcpy(f.bytes,"FLK2",4);f.bytes[4]=1;f.bytes[5]=uint8_t(kind);put16(f.bytes+6,n);
    memcpy(f.bytes+8,sender,6);memcpy(f.bytes+14,target,6);memcpy(f.bytes+20,nonce,16);put32(f.bytes+36,sequence);
    if(n) memcpy(f.bytes+Header,body,n);
    f.size=Header+n+Tag;
    return true;
}
inline int label_index(char row,char col) {return row>='A'&&row<='D'&&col>='1'&&col<='4'?(row-'A')*4+col-'1':-1;}
enum class Decision {Write,Duplicate,Reject};
struct TransferOrder {
    uint32_t total=0,received=0,next_sequence=2,last_offset=0,last_length=0;
    void begin(uint32_t size) {*this={};total=size;next_sequence=2;}
    Decision accept(uint32_t seq,uint32_t offset,uint32_t length) const {
        if(length==0 || length>128)return Decision::Reject;
        if(seq==next_sequence-1 && last_length && offset==last_offset && length==last_length)return Decision::Duplicate;
        if(seq!=next_sequence || offset!=received || received>total || length>total-received)return Decision::Reject;
        return Decision::Write;
    }
    void written(uint32_t seq,uint32_t offset,uint32_t length){last_offset=offset;last_length=length;received+=length;next_sequence=seq+1;}
    bool complete()const{return total && received==total;}
};
// Health payload: label[2], core_ok, receiver_version, version[16], image_sha[32],
// boots:u32@52, uptime_ms:u32@56, ota_state:u8@60, flash:u32@61,
// psram:u32@65, free_internal:u32@69, channel:u8@73, rssi:i8@74,
// sd_pass:u8@75, sd_bytes:u64@76, sensor_bits@84, audio_bits@85,
// panel_driver_ok@86, temp_centidegrees:i16@87, humidity_centipercent:u16@89,
// active_slot:u8@91, reset_reason:u8@92; reserved zero to96.
// BEGIN payload73: file_bytes:u32 + whole_file_sha256[32] + ESP_image_sha256[32]
// + target_tag ASCII WS32[4] + required_receiver_version:u8 (1).
// DATA: offset:u32 +1..128bytes. ACK: code:u8 + bytes_written:u32.
// OPEN echoes requester nonce/sequence in CHALLENGE; challenge body is fresh16bytes.
// All session requests/ACKs use that node challenge as header nonce; BEGIN seq1.
}
