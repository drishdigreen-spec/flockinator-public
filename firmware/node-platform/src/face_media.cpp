#include "face_media.h"
#include "face_pack.h"
#include "faces_meta.h"
#include "esp_heap_caps.h"
#include "mbedtls/sha256.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <atomic>
#include <cstdio>
#include <cstring>
#include <sys/stat.h>
#include <cerrno>
extern const uint8_t pack_start[] asm("_binary_faces_pack_start");
extern const uint8_t pack_end[] asm("_binary_faces_pack_end");
namespace {
std::atomic<const uint8_t*> cached{nullptr};
std::atomic<int> result{0}; // pending, cached, seeded, no SD, memory, invalid, IO
bool verify(const uint8_t* p,size_t n){
 if(!node::valid_face_pack(p,n))return false;
 uint8_t digest[32];char hex[65];if(mbedtls_sha256(p,n,digest,0))return false;
 for(int i=0;i<32;i++)snprintf(hex+i*2,3,"%02x",digest[i]);return !strcmp(hex,FacesSha);
}
bool read_file(const char* path,uint8_t* data,size_t n){
 FILE* f=fopen(path,"rb");if(!f)return false;
 bool ok=fread(data,1,n,f)==n && fgetc(f)==EOF;if(fclose(f))ok=false;return ok&&verify(data,n);
}
bool directory(const char* p){return mkdir(p,0755)==0||errno==EEXIST;}
}
const uint8_t* face_media_frame(unsigned index){
 const uint8_t* p=cached.load();if(!p)p=pack_start;
 const size_t size=pack_end-pack_start;
 if(!node::valid_face_pack(p,size))return nullptr;
 if(index>=node::face_u32(p+8))index=32;
 if(index>=node::face_u32(p+8))index=0;
 return p+16+index*8192;
}
bool face_media_cached(){return cached.load()!=nullptr;}
void face_media_load_sd(){
 if(cached.load())return;
 const size_t n=pack_end-pack_start;
 if(!verify(pack_start,n)){result=5;return;}
 auto* data=static_cast<uint8_t*>(heap_caps_malloc(n,MALLOC_CAP_SPIRAM));
 if(!data){result=4;return;}
 char dir[180],path[200],temporary[210];
 snprintf(dir,sizeof(dir),"/sd/flockinator/media/faces/%s",FacesSha);
 snprintf(path,sizeof(path),"%s/faces.pack",dir);snprintf(temporary,sizeof(temporary),"%s/incomplete.tmp",dir);
 if(read_file(path,data,n)){cached.store(data);result=1;return;}
 if(!directory("/sd/flockinator")||!directory("/sd/flockinator/media")||!directory("/sd/flockinator/media/faces")||!directory(dir)){free(data);result=3;return;}
 FILE* f=fopen(temporary,"wb");bool ok=f!=nullptr;
 if(f){for(size_t offset=0;offset<n&&ok;offset+=4096){size_t length=n-offset<4096?n-offset:4096;ok=fwrite(pack_start+offset,1,length,f)==length;vTaskDelay(1);}if(fflush(f))ok=false;if(fclose(f))ok=false;}
 if(ok)ok=read_file(temporary,data,n);
 if(ok){ // Only replace this exact digest-owned incomplete/corrupt pack.
  remove(path);ok=rename(temporary,path)==0;
 }
 if(ok){cached.store(data);result=2;}else{free(data);result=6;}
}
void face_media_json(cJSON* root){
 static const char* names[]={"PENDING","VERIFIED_SD","SEEDED_VERIFIED_SD","SD_UNAVAILABLE","CACHE_ALLOCATION_FAILED","BUNDLED_PACK_INVALID","SD_COPY_FAILED"};
 auto* j=cJSON_AddObjectToObject(root,"face_media");int r=result.load();
 cJSON_AddStringToObject(j,"source",face_media_cached()?"sd_psram":"bundled_flash");
 cJSON_AddStringToObject(j,"result",names[r]);cJSON_AddStringToObject(j,"sha256",FacesSha);
 cJSON_AddNumberToObject(j,"pack_bytes",pack_end-pack_start);cJSON_AddBoolToObject(j,"verified",r==1||r==2);
}
