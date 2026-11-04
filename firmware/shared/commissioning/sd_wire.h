#pragma once
#include "wire.h"
namespace flocksd {
constexpr size_t ReportSize=144;
// Request: op byte (0=status, 1=prepare, 2=format+quick, 3=format+full).
// Destructive requests append card_id decoded from 80 hex chars, then 16-byte permit.
// Reply is authenticated and echoes the request's random nonce and sequence.
// [0] command code, [1] layout version=1, [2] job phase, [3] flags:
// responding=1, FAT32=2, isolated IO=4, full=8, worker-ready=16.
// job:u32@4, probe_error:u32@8, fat_result:u32@12, card_id[40]@16,
// permit[16]@56, capacity:u64@72, fs_bytes:u64@80, free:u64@88,
// target:u64@96, written:u64@104, read:u64@112, write_ms:u32@120,
// read_ms:u32@124, failed_offset:u64@128, permit_remaining_ms:u32@136,
// error_id:u8@140; reserved to 144. Job phases match names below.
inline void put64(uint8_t* p,uint64_t v){for(unsigned i=0;i<8;++i)p[i]=v>>(8*i);}
inline uint64_t get64(const uint8_t* p){return uint64_t(flockwire::get32(p))|uint64_t(flockwire::get32(p+4))<<32;}
inline const char* phase(unsigned n){static const char* names[]={"IDLE","INSPECTING","READY","FORMATTING","WRITING","READING","PASSED","FAILED","INTERRUPTED"};return n<9?names[n]:"UNKNOWN";}
inline const char* error(unsigned n){
    static const char* names[]={"","card_not_responding","card_changed","unsupported_geometry","filesystem_driver_unavailable","format_buffer_unavailable","format_or_mbr_verification_failed","test_directory_failed","invalid_file_count","test_create_failed","test_close_failed","invalid_test_extent","test_buffer_unavailable","test_open_failed","test_file_size_changed","test_read_failed","test_write_failed","test_data_mismatch","test_sync_failed","test_cleanup_failed","cannot_record_destructive_intent","format_or_test_failed","cannot_record_result","power_loss_or_restart"};
    return n<sizeof(names)/sizeof(names[0])?names[n]:"unknown_storage_error";
}
inline uint8_t error_id(const char* value){for(unsigned i=0;i<24;++i)if(!strcmp(value,error(i)))return i;return 255;}
inline bool request_valid(const uint8_t* p,size_t n){return p&&n&&p[0]<=3&&n==(p[0]<2?1u:57u);}
inline bool report_valid(const uint8_t* p,size_t n){return p&&n==ReportSize&&p[0]<=6&&p[1]==1&&p[2]<=8&&!(p[3]&~31u);}
}
