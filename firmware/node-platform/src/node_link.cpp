#include "node_link.h"
#include "mission.h"
#include "storage.h"
#include "commissioning/sd_wire.h"
#include "maintenance.h"
#include "network.h"
#include "ota_policy.h"
#include "commissioning/crypto.h"
#include "esp_now.h"
#include "esp_wifi.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_ota_ops.h"
#include "esp_app_desc.h"
#include "esp_app_format.h"
#include "mbedtls/sha256.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include <atomic>
#include <cstring>
#include <cstdio>
#include <algorithm>

namespace {
using namespace flockwire;
constexpr uint32_t SessionTimeoutMs=node::LinkTimeoutMs;
static_assert(ESP_CHIP_ID_ESP32S3==9 && ESP_IMAGE_HEADER_MAGIC==0xe9,"Update the image policy for a changed ESP image format");
struct Received { uint8_t source[6]; uint16_t length; uint8_t bytes[MaxFrame]; };
QueueHandle_t inbox;
SemaphoreHandle_t health_guard;
uint8_t own[6]{},health[recon::HealthSize]{};
std::atomic<bool> ready{false},active{false};
std::atomic<uint32_t> overflow{0},rejected{0},polls{0},last_poll{0},send_failures{0};
std::atomic<uint32_t> transfers{0},timeouts{0},written_bytes{0},commits{0};
uint8_t challenger[6]{},challenge[16]{},open_tag[32]{};
bool have_open=false,challenge_available=false;
uint32_t challenge_at=0;
Frame challenge_reply;
bool have_sd_reply=false;
uint8_t sd_tag[32]{};
Frame sd_reply;
Frame mission_reply;uint8_t mission_tag[32]{};bool have_mission_reply=false;
struct Session {
    uint8_t source[6]{},nonce[16]{},file_sha[32]{},image_sha[32]{},last_tag[32]{};
    uint32_t touched=0;
    esp_ota_handle_t handle=0;
    const esp_partition_t* slot=nullptr;
    TransferOrder order;
    mbedtls_sha256_context hash;
    Frame last_ack;
} session;

uint32_t now_ms() { return static_cast<uint32_t>(esp_timer_get_time()/1000); }
bool peer(const uint8_t* mac) {
    if(esp_now_is_peer_exist(mac)) return true;
    esp_now_peer_info_t p{};
    memcpy(p.peer_addr,mac,6); p.ifidx=WIFI_IF_STA; p.channel=0;
    return esp_now_add_peer(&p)==ESP_OK;
}
void send(const uint8_t* target,const Frame& frame) {
    if(!peer(target) || esp_now_send(target,frame.bytes,frame.size)!=ESP_OK) ++send_failures;
}
Frame response(const View& req,Kind kind,const uint8_t* payload,size_t length,const uint8_t* key) {
    Frame f;
    encode(f,kind,own,req.sender,req.nonce,req.sequence,payload,length);
    sign(f,key);
    return f;
}
Frame ack(const View& req,Code code,const uint8_t* key) {
    uint8_t payload[5]{static_cast<uint8_t>(code)};
    put32(payload+1,written_bytes.load());
    auto f=response(req,Kind::Ack,payload,sizeof(payload),key);
    send(req.sender,f);
    return f;
}
void fail(const View& req,Code code,const uint8_t* key) { ++rejected; ack(req,code,key); }
void stop() {
    if(!active.exchange(false)) return;
    if(session.handle) esp_ota_abort(session.handle);
    session.handle=0;
    mbedtls_sha256_free(&session.hash);
    maintenance_release_update();
}
void handle(const Received& received,const uint8_t* key) {
    View req{};
    if(!authenticate(received.bytes,received.length,key,req) ||
       !equal(req.sender,received.source,6) || !equal(req.target,own,6) ||
       equal(req.sender,own,6)) { ++rejected; return; }
    const uint32_t now=now_ms();
    if(req.kind==Kind::SdRequest) {
        if(!flocksd::request_valid(req.payload,req.length)){fail(req,Code::Invalid,key);return;}
        // Retries of the identical last command return its original acceptance;
        // a consumed card permit can never launch a second format.
        if(have_sd_reply&&equal(req.tag,sd_tag,32)){send(req.sender,sd_reply);return;}
        uint32_t job=0;const char* error=nullptr;
        if(req.payload[0]){
            char card_id[81]{},token[33]{};
            if(req.length==57){
                for(unsigned i=0;i<40;++i)snprintf(card_id+2*i,3,"%02x",req.payload[1+i]);
                for(unsigned i=0;i<16;++i)snprintf(token+2*i,3,"%02x",req.payload[41+i]);
            }
            error=storage_request(req.payload[0],card_id,token,job);
        }
        uint8_t body[flocksd::ReportSize];
        storage_report(body,error?uint8_t(!strcmp(error,"maintenance_busy")?Code::Busy:Code::Invalid):uint8_t(Code::Ok),job);
        sd_reply=response(req,Kind::SdReply,body,sizeof(body),key);memcpy(sd_tag,req.tag,32);have_sd_reply=true;
        send(req.sender,sd_reply);return;
    }
    if(req.kind==Kind::Poll) {
        if(req.length) { fail(req,Code::Invalid,key); return; }
        uint8_t body[recon::HealthSize];
        xSemaphoreTake(health_guard,portMAX_DELAY);
        memcpy(body,health,sizeof(body));
        xSemaphoreGive(health_guard);
        mission_health(body);
        body[3]=1; // Only the running, key-provisioned worker advertises this capability.
        put32(body+56,now);
        body[73]=network_channel();
        wifi_ap_record_t ap{};
        body[74]=esp_wifi_sta_get_ap_info(&ap)==ESP_OK?static_cast<uint8_t>(ap.rssi):0;
        send(req.sender,response(req,Kind::Health,body,sizeof(body),key));
        ++polls; last_poll=now;
        return;
    }
    if(req.kind==Kind::Open) {
        if(req.length) { fail(req,Code::Invalid,key); return; }
        if(have_open && equal(req.tag,open_tag,32)) {
            if(challenge_available && now-challenge_at<SessionTimeoutMs) send(req.sender,challenge_reply);
            else fail(req,Code::Invalid,key); // A consumed/expired OPEN cannot revive its challenge.
            return;
        }
        if(maintenance_busy()) { fail(req,Code::Busy,key); return; }
        memcpy(challenger,req.sender,6); memcpy(open_tag,req.tag,32);
        esp_fill_random(challenge,sizeof(challenge));
        challenge_at=now; have_open=true; challenge_available=true;
        challenge_reply=response(req,Kind::Challenge,challenge,sizeof(challenge),key);
        send(req.sender,challenge_reply);
        return;
    }
    if(req.kind==Kind::Mission){
        if(have_mission_reply&&equal(req.tag,mission_tag,32)){send(req.sender,mission_reply);return;}
        if(!challenge_available||now-challenge_at>=SessionTimeoutMs||!equal(req.sender,challenger,6)||!equal(req.nonce,challenge,16)||req.sequence!=1){fail(req,Code::Invalid,key);return;}
        challenge_available=false;
        recon::Config config;bool start=false;uint32_t delay=0;
        Code code=maintenance_busy()?Code::Busy:!recon::command_decode(req.payload,req.length,config,start,delay)?Code::Invalid:mission_apply(config,start,delay)?Code::Ok:Code::Invalid;
        uint8_t result[5]{uint8_t(code)};put32(result+1,config.run);
        mission_reply=response(req,Kind::MissionReply,result,sizeof(result),key);memcpy(mission_tag,req.tag,32);have_mission_reply=true;send(req.sender,mission_reply);return;
    }
    if(active && equal(req.sender,session.source,6) && equal(req.nonce,session.nonce,16) &&
       equal(req.tag,session.last_tag,32)) {
        session.touched=now;
        send(req.sender,session.last_ack); // Only the byte-identical last accepted request is idempotent.
        return;
    }
    if(req.kind==Kind::Begin) {
        if(active || maintenance_busy()) { fail(req,Code::Busy,key); return; }
        if(!challenge_available || now-challenge_at>=SessionTimeoutMs ||
           !equal(req.sender,challenger,6) || !equal(req.nonce,challenge,16) ||
           req.sequence!=1 || req.length!=73) { fail(req,Code::Invalid,key); return; }
        challenge_available=false; // Consume before any flash operation, including a failed BEGIN.
        const auto* slot=esp_ota_get_next_update_partition(nullptr);
        uint32_t bytes=get32(req.payload);
        if(memcmp(req.payload+68,"WS32",4) || req.payload[72]!=1) { fail(req,Code::Unsupported,key); return; }
        if(!slot || slot==esp_ota_get_running_partition() || !node::valid_manifest(req.payload,req.length,slot->size)) { fail(req,Code::Invalid,key); return; }
        if(!maintenance_claim_update()) { fail(req,Code::Busy,key); return; }
        session={}; session.slot=slot;
        memcpy(session.source,req.sender,6); memcpy(session.nonce,req.nonce,16);
        memcpy(session.file_sha,req.payload+4,32); memcpy(session.image_sha,req.payload+36,32);
        mbedtls_sha256_init(&session.hash);
        mbedtls_sha256_starts(&session.hash,0);
        session.order.begin(bytes); active=true; written_bytes=0;
        if(esp_ota_begin(slot,bytes,&session.handle)!=ESP_OK) { stop(); fail(req,Code::Storage,key); return; }
        session.touched=now_ms(); ++transfers;
        memcpy(session.last_tag,req.tag,32);
        session.last_ack=ack(req,Code::Ok,key);
        return;
    }
    if(!active || !equal(req.sender,session.source,6) || !equal(req.nonce,session.nonce,16)) {
        fail(req,Code::Invalid,key); return;
    }
    if(req.kind==Kind::Abort) {
        if(req.length || req.sequence!=session.order.next_sequence) { fail(req,Code::Order,key); return; }
        stop(); ack(req,Code::Ok,key); return;
    }
    if(req.kind==Kind::Data) {
        if(req.length<5 || req.length>132) { fail(req,Code::Invalid,key); return; }
        uint32_t offset=get32(req.payload),length=req.length-4;
        if(session.order.accept(req.sequence,offset,length)!=Decision::Write) {
            fail(req,Code::Order,key); return; // Changed duplicates never get an OK acknowledgement.
        }
        if(offset==0 && !node::valid_first_chunk(req.payload+4,length)) {
            stop(); fail(req,Code::Unsupported,key); return;
        }
        if(esp_ota_write(session.handle,req.payload+4,length)!=ESP_OK ||
           mbedtls_sha256_update(&session.hash,req.payload+4,length)!=0) {
            stop(); fail(req,Code::Storage,key); return;
        }
        session.order.written(req.sequence,offset,length);
        written_bytes=session.order.received; session.touched=now_ms();
        memcpy(session.last_tag,req.tag,32);
        session.last_ack=ack(req,Code::Ok,key);
        return;
    }
    if(req.kind==Kind::Commit) {
        if(req.length || req.sequence!=session.order.next_sequence || !session.order.complete()) {
            fail(req,Code::Order,key); return;
        }
        uint8_t digest[32];
        if(mbedtls_sha256_finish(&session.hash,digest)!=0 || !equal(digest,session.file_sha,32)) {
            stop(); fail(req,Code::Digest,key); return;
        }
        esp_err_t result=esp_ota_end(session.handle);
        session.handle=0; // esp_ota_end releases the handle on either outcome.
        esp_app_desc_t app{};
        if(result==ESP_OK) result=esp_ota_get_partition_description(session.slot,&app);
        if(result==ESP_OK && strncmp(app.project_name,esp_app_get_description()->project_name,sizeof(app.project_name))) result=ESP_ERR_INVALID_ARG;
        if(result==ESP_OK) result=esp_partition_get_sha256(session.slot,digest);
        if(result==ESP_OK && !equal(digest,session.image_sha,32)) result=ESP_ERR_INVALID_CRC;
        if(result==ESP_OK) result=esp_ota_set_boot_partition(session.slot);
        if(result!=ESP_OK) { stop(); fail(req,Code::Digest,key); return; }
        ++commits;
        ack(req,Code::Ok,key);
        // Keep the update lease until reboot, preventing another writer from replacing this image.
        vTaskDelay(pdMS_TO_TICKS(500)); esp_restart();
        return;
    }
    fail(req,Code::Unsupported,key);
}
void worker(void*) {
    Received received{};
    while(true) {
        if(active && node::link_expired(now_ms(),session.touched)) { ++timeouts; stop(); }
        if(xQueueReceive(inbox,&received,pdMS_TO_TICKS(100))==pdTRUE) {
            uint8_t key[32]{};
            if(maintenance_copy_key(key)) handle(received,key);
            else ++rejected;
            memset(key,0,sizeof(key));
        }
    }
}
const cJSON* field(const cJSON* obj,const char* key) { return cJSON_GetObjectItemCaseSensitive(obj,key); }
const char* text(const cJSON* obj,const char* key) { auto* f=field(obj,key); return cJSON_IsString(f)?f->valuestring:""; }
double number(const cJSON* obj,const char* key) { auto* f=field(obj,key); return cJSON_IsNumber(f)?f->valuedouble:0; }
bool pass(const cJSON* obj,const char* key) { return !strcmp(text(obj,key),"PASS"); }
}

void node_link_init() {
    if(!network_now_ready() || esp_wifi_get_mac(WIFI_IF_STA,own)!=ESP_OK) return;
    health_guard=xSemaphoreCreateMutex();
    inbox=xQueueCreate(8,sizeof(Received));
    if(!health_guard || !inbox) return;
    ready=xTaskCreate(worker,"flock_link",8192,nullptr,3,nullptr)==pdPASS;
}
bool node_link_ready() { return ready; }

void node_link_receive(const uint8_t source[6],const uint8_t* data,size_t length) {
    if(!ready || !inbox || length>flockwire::MaxFrame) return;
    flockwire::View view{};
    if(!flockwire::decode(data,length,view)) return;
    Received received{}; memcpy(received.source,source,6);
    received.length=length; memcpy(received.bytes,data,length);
    if(xQueueSend(inbox,&received,0)!=pdTRUE) ++overflow;
}

void node_link_publish(cJSON* status) {
    if(!health_guard) return;
    uint8_t body[recon::HealthSize]{};
    const char* label=text(status,"label");
    if(strlen(label)==2) memcpy(body,label,2);
    body[2]=pass(status,"identity_nvs") && pass(status,"psram_sample") && maintenance_ready() && ready;
    strncpy(reinterpret_cast<char*>(body+4),text(status,"firmware"),15);
    const char* digest=text(status,"app_sha256");
    if(strlen(digest)==64) for(int i=0;i<32;++i) { unsigned v=0; if(sscanf(digest+2*i,"%2x",&v)==1) body[20+i]=v; }
    flockwire::put32(body+52,number(status,"boot_count"));
    flockwire::put32(body+56,number(status,"uptime_ms"));
    body[60]=number(status,"ota_state");
    flockwire::put32(body+61,number(status,"flash_bytes"));
    flockwire::put32(body+65,number(status,"psram_bytes"));
    flockwire::put32(body+69,number(status,"free_internal"));
    const auto* net=field(status,"network"); const auto* sd=field(status,"sd");
    const auto* sensors=field(status,"sensors"); const auto* audio=field(status,"audio");
    body[73]=number(net,"channel"); body[74]=static_cast<int8_t>(number(net,"rssi_dbm"));
    body[75]=pass(sd,"state");
    uint64_t capacity=number(sd,"capacity_bytes");
    for(int i=0;i<8;++i) body[76+i]=capacity>>(8*i);
    body[84]=(pass(sensors,"shtc3")?1:0)|(pass(sensors,"qmi8658")?2:0)|(pass(sensors,"rtc_clock")?4:0);
    body[85]=(pass(audio,"speaker_codec")?1:0)|(pass(audio,"microphone_codec")?2:0)|(pass(audio,"capture")?4:0);
    body[86]=pass(field(status,"panel"),"driver");
    flockwire::put16(body+87,static_cast<int16_t>(number(sensors,"temperature_c")*100));
    flockwire::put16(body+89,number(sensors,"humidity_percent")*100);
    body[91]=!strcmp(text(status,"running_partition"),"ota_1")?1:0;
    body[92]=number(status,"reset_reason");
    mission_health(body);
    body[93]=1; // SD maintenance extension, independent of OTA receiver version.
    xSemaphoreTake(health_guard,portMAX_DELAY); memcpy(health,body,sizeof(body)); xSemaphoreGive(health_guard);
}

void node_link_json(cJSON* status) {
    auto* obj=cJSON_AddObjectToObject(status,"commissioning_link");
    uint8_t key[32]{}; bool keyed=maintenance_copy_key(key); memset(key,0,sizeof(key));
    cJSON_AddNumberToObject(obj,"protocol_version",1);
    cJSON_AddNumberToObject(obj,"receiver_version",ready && keyed?1:0);
    cJSON_AddBoolToObject(obj,"worker_ready",ready);
    cJSON_AddBoolToObject(obj,"wifi_ota_supported",maintenance_ready());
    cJSON_AddBoolToObject(obj,"espnow_receiver_supported",ready && keyed);
    auto seen=last_poll.load();
    cJSON_AddStringToObject(obj,"console_link",seen?(now_ms()-seen<30000?"AUTHENTICATED_POLL":"STALE"):"UNSEEN");
    cJSON_AddStringToObject(obj,"espnow_deployment_verified","HOST_EVIDENCE_REQUIRED");
    cJSON_AddNumberToObject(obj,"authenticated_polls",polls);
    cJSON_AddNumberToObject(obj,"last_poll_ms",seen);
    cJSON_AddNumberToObject(obj,"queue_overflow",overflow);
    cJSON_AddNumberToObject(obj,"rejected_frames",rejected);
    cJSON_AddNumberToObject(obj,"send_failures",send_failures);
    cJSON_AddBoolToObject(obj,"transfer_active",active);
    cJSON_AddNumberToObject(obj,"bytes_written",written_bytes);
    cJSON_AddNumberToObject(obj,"transfer_starts",transfers);
    cJSON_AddNumberToObject(obj,"transfer_timeouts",timeouts);
    cJSON_AddNumberToObject(obj,"committed_images",commits);
}
