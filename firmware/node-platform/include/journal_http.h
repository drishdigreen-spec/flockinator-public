#pragma once
// Included by maintenance.cpp after its authenticated-request helpers.
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
#include "esp_heap_caps.h"

namespace journal {
constexpr size_t Limit = 128 * 1024;
struct StorageLease { ~StorageLease(){ maintenance_release_storage(); } };

static bool hash_file(const char* path, const char* expected, size_t bytes) {
    FILE* file = fopen(path,"rb");
    if (!file) return false;
    mbedtls_sha256_context hash;
    mbedtls_sha256_init(&hash); mbedtls_sha256_starts(&hash,0);
    uint8_t chunk[1024], digest[32]; size_t count=0, n;
    while (count<=bytes && (n=fread(chunk,1,sizeof(chunk),file))>0) {
        count+=n; mbedtls_sha256_update(&hash,chunk,n);
    }
    bool ok=!ferror(file) && count==bytes;
    fclose(file); mbedtls_sha256_finish(&hash,digest); mbedtls_sha256_free(&hash);
    char actual[65]; hex(digest,32,actual);
    return ok && !strcmp(expected,actual);
}

static esp_err_t handle(httpd_req_t* req) {
    char signed_hash[65];
    xSemaphoreTake(guard,portMAX_DELAY);
    bool auth=authenticate(req,signed_hash);
    xSemaphoreGive(guard);
    if (!auth) return httpd_resp_send_err(req,HTTPD_401_UNAUTHORIZED,"Authentication failed");
    bool read=!strcmp(req->uri,"/v1/journal/read");
    size_t size=req->content_len;
    if (!size || size>Limit || (read && size!=64))
        return httpd_resp_send_err(req,HTTPD_400_BAD_REQUEST,"Invalid journal length");
    auto* body=static_cast<uint8_t*>(heap_caps_malloc(size+1,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
    if (!body) return unavailable(req);
    struct Buffer { void* p; ~Buffer(){free(p);} } cleanup{body};
    for (size_t got=0;got<size;) {
        int n=httpd_req_recv(req,reinterpret_cast<char*>(body+got),size-got);
        if (n<=0) return ESP_FAIL;
        got+=n;
    }
    body[size]=0;
    uint8_t digest[32]; char actual[65];
    mbedtls_sha256(body,size,digest,0); hex(digest,32,actual);
    if (strcmp(actual,signed_hash))
        return httpd_resp_send_err(req,HTTPD_400_BAD_REQUEST,"Digest mismatch");
    const char* key=read?reinterpret_cast<char*>(body):signed_hash;
    if (read && !unhex(key,digest,32))
        return httpd_resp_send_err(req,HTTPD_400_BAD_REQUEST,"Invalid journal ID");
    if (!maintenance_claim_storage()) return unavailable(req);
    StorageLease lease;
    char path[96]; snprintf(path,sizeof(path),"/sd/JOURNALS/%s.jsonl",key);
    if (read) {
        struct stat entry{};
        if (stat(path,&entry)!=0) return httpd_resp_send_err(req,HTTPD_404_NOT_FOUND,"Unknown journal");
        if (entry.st_size<=0 || entry.st_size>Limit) return unavailable(req);
        FILE* f=fopen(path,"rb");
        if (!f) return unavailable(req);
        httpd_resp_set_type(req,"application/x-ndjson");
        size_t n; char chunk[1024]; esp_err_t err=ESP_OK;
        while ((n=fread(chunk,1,sizeof(chunk),f)) && err==ESP_OK)
            err=httpd_resp_send_chunk(req,chunk,n);
        if (ferror(f)) err=ESP_FAIL;
        fclose(f);
        return err==ESP_OK?httpd_resp_send_chunk(req,nullptr,0):err;
    }
    if (mkdir("/sd/JOURNALS",0700)!=0 && errno!=EEXIST) return unavailable(req);
    struct stat existing{};
    if (stat(path,&existing)==0) {
        if (!hash_file(path,key,size)) return unavailable(req);
    } else {
        if (errno!=ENOENT) return unavailable(req);
        const char* temp="/sd/JOURNALS/PENDING.TMP";
        FILE* f=fopen(temp,"wb");
        if (!f) return unavailable(req);
        bool ok=fwrite(body,1,size,f)==size;
        if (fclose(f)!=0) ok=false;
        // Reopen the card file before publishing; a retry can verify an existing file.
        if (!ok || !hash_file(temp,key,size) || rename(temp,path)!=0) {
            unlink(temp); return unavailable(req);
        }
    }
    char reply[120]; snprintf(reply,sizeof(reply),"{\"ok\":true,\"sha256\":\"%s\",\"bytes\":%u}",key,unsigned(size));
    return answer(req,reply);
}
}
