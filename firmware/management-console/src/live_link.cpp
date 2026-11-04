#include <Arduino.h>
#include <atomic>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <Preferences.h>
#include <SD.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_mac.h>
#include <esp_heap_caps.h>
#include <mbedtls/sha256.h>
#include "live_link.h"
#include "live_policy.h"
#include "hardware.h"
#include "../../shared/commissioning/crypto.h"
#include "../../shared/commissioning/sd_wire.h"

namespace flockinator {
namespace {
using namespace flockwire;
constexpr uint32_t MaxImage=8*1024*1024;
constexpr char ExpectedMac[]="00:11:22:33:44:55";
uint32_t health_poll_retries=0;
struct Binding {uint8_t mac[6]{},key[32]{},nonce[16]{};uint32_t sequence=0,poll_at=0,pending_at=0,retry_at=0;uint8_t retries=0;bool pending=false;};
struct Packet {uint8_t source[6];uint16_t size;uint8_t bytes[MaxFrame];};
LiveSnapshot state;
Binding bindings[16];
uint8_t own[6]; char own_text[18],boot_id[33];
SemaphoreHandle_t mutex;
QueueHandle_t queue;
Preferences prefs;
bool ready=false, paused=false, sd_ready=false;
uint32_t serial_write_failures=0,transfer_retries=0;
std::atomic<uint32_t> rx_queue_overflows{0};
File upload;
uint32_t upload_size=0,upload_offset=0,upload_last=0;
uint8_t upload_sha[32];char upload_name[65]{},upload_path[100]{};
char selected_image[65]{};
uint8_t selected_digest[32]{};
struct Deployment {
    enum Stage {Idle,Opening,Beginning,Sending,Committing,Verifying} stage=Idle;
    int node=-1; File file; Frame frame;
    uint8_t nonce[16]{},file_sha[32]{},image_sha[32]{};
    uint32_t total=0,offset=0,sequence=0,sent=0,wait_started=0,verify_started=0,previous_boots=0;unsigned tries=0;
} transfer;
struct SdRelay {
    bool pending=false,complete=false,timed_out=false;
    int node=-1;uint32_t sequence=0,sent=0,started=0;
    uint8_t nonce[16]{},report[flocksd::ReportSize]{};
    Frame frame;
} sd_relay;
struct MissionDispatch {
    bool active=false,start=false,opening=false;int node=-1;
    uint32_t deadline=0,sent=0,began=0;uint8_t nonce[16]{};
    recon::Config command;Frame frame;
} mission_dispatch;
void emit(Frame&,int);
void next_mission_node();
void mission_send(Kind kind,const uint8_t* body,size_t length,uint32_t sequence){
    auto& d=mission_dispatch;encode(d.frame,kind,own,bindings[d.node].mac,d.nonce,sequence,body,length);emit(d.frame,d.node);d.sent=d.began=millis();
}


bool unhex(const char* s,uint8_t* out,size_t n) {
    if(!s || strlen(s)!=n*2)return false;
    auto digit=[](char c)->int {if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;};
    for(size_t i=0;i<n;++i) {int a=digit(s[2*i]),b=digit(s[2*i+1]);if(a<0||b<0)return false;out[i]=uint8_t(a*16+b);}return true;
}
void hex(const uint8_t* data,size_t n,char* out) {static const char d[]="0123456789abcdef";for(size_t i=0;i<n;++i){out[2*i]=d[data[i]>>4];out[2*i+1]=d[data[i]&15];}out[n*2]=0;}
void mac_text(const uint8_t* m,char* out){snprintf(out,18,"%02X:%02X:%02X:%02X:%02X:%02X",m[0],m[1],m[2],m[3],m[4],m[5]);}
bool mac_parse(const char* s,uint8_t* out) {if(!s||strlen(s)!=17)return false;char flat[13]{};for(int i=0;i<6;++i){if(i<5&&s[i*3+2]!=':')return false;flat[i*2]=s[i*3];flat[i*2+1]=s[i*3+1];}return unhex(flat,out,6)&&!(out[0]&1);}

String image_path(const char* name){return String("/flockinator/images/")+name;}
void lock(){xSemaphoreTake(mutex,portMAX_DELAY);}void unlock(){xSemaphoreGive(mutex);}
void label_for(int i,char* out){out[0]='A'+i/4;out[1]='1'+i%4;out[2]=0;}
void receive(const uint8_t* source,const uint8_t* data,int length) {
    if(length<int(Header+Tag)||length>int(MaxFrame))return;
    Packet p{};memcpy(p.source,source,6);p.size=length;memcpy(p.bytes,data,length);if(xQueueSend(queue,&p,0)!=pdTRUE)++rx_queue_overflows;
}
bool add_peer(const uint8_t* mac){if(esp_now_is_peer_exist(mac))return true;esp_now_peer_info_t p{};memcpy(p.peer_addr,mac,6);p.ifidx=WIFI_IF_STA;p.channel=0;return esp_now_add_peer(&p)==ESP_OK;}
void emit(Frame& f,int index){sign(f,bindings[index].key);esp_now_send(bindings[index].mac,f.bytes,f.size);}
void fail(const char* reason) {
    if(transfer.stage!=Deployment::Idle&&transfer.stage!=Deployment::Opening&&transfer.stage!=Deployment::Verifying) {
        Frame abort;encode(abort,Kind::Abort,own,bindings[transfer.node].mac,transfer.nonce,transfer.sequence+1,nullptr,0);emit(abort,transfer.node);
    }
    transfer.file.close();transfer.stage=Deployment::Idle;state.busy=false;snprintf(state.deployment,sizeof(state.deployment),"Failed: %s / allow 20s cleanup",reason);
}
void send_stage(Kind kind,const uint8_t* data,size_t size,uint32_t sequence) {
    transfer.sequence=sequence;encode(transfer.frame,kind,own,bindings[transfer.node].mac,transfer.nonce,sequence,data,size);
    emit(transfer.frame,transfer.node);transfer.sent=millis();transfer.wait_started=transfer.sent;transfer.tries=1;
}
void next_data() {
    if(transfer.offset==transfer.total) {transfer.stage=Deployment::Committing;send_stage(Kind::Commit,nullptr,0,transfer.sequence+1);return;}
    uint8_t body[132];put32(body,transfer.offset);size_t n=std::min<uint32_t>(128,transfer.total-transfer.offset);
    if(transfer.file.read(body+4,n)!=int(n)){fail("SD read");return;}
    transfer.stage=Deployment::Sending;send_stage(Kind::Data,body,n+4,transfer.sequence+1);
}
bool inspect_image(File& file,uint8_t* full,uint8_t* embedded) {
    if(!file||file.size()<288||file.size()>MaxImage)return false;
    uint8_t header[112];file.seek(0);if(file.read(header,sizeof(header))!=sizeof(header)||header[0]!=0xe9||get16(header+12)!=9||get32(header+32)!=0xabcd5432||memcmp(header+80,"flockinator_node",17))return false;
    mbedtls_sha256_context hash,image_hash;mbedtls_sha256_init(&hash);mbedtls_sha256_init(&image_hash);mbedtls_sha256_starts_ret(&hash,0);mbedtls_sha256_starts_ret(&image_hash,0);
    uint8_t chunk[512],calculated[32];file.seek(0);uint32_t remain=file.size(),position=0,prefix=file.size()-32;
    while(remain) {size_t n=std::min<uint32_t>(sizeof(chunk),remain);if(file.read(chunk,n)!=int(n)){mbedtls_sha256_free(&hash);mbedtls_sha256_free(&image_hash);return false;}mbedtls_sha256_update_ret(&hash,chunk,n);if(position<prefix)mbedtls_sha256_update_ret(&image_hash,chunk,std::min<uint32_t>(n,prefix-position));position+=n;remain-=n;if((position&32767)==0)vTaskDelay(1);}
    mbedtls_sha256_finish_ret(&hash,full);mbedtls_sha256_finish_ret(&image_hash,calculated);mbedtls_sha256_free(&hash);mbedtls_sha256_free(&image_hash);
    file.seek(file.size()-32);if(file.read(embedded,32)!=32||!equal(calculated,embedded,32))return false;file.seek(0);return true;
}
bool persist_selection(const char* name,const uint8_t* digest) {
    uint8_t record[97]{};strlcpy(reinterpret_cast<char*>(record),name,65);memcpy(record+65,digest,32);
    if(prefs.putBytes("selection",record,sizeof(record))!=sizeof(record))return false;
    // The new atomic record binds name and digest. Remove the legacy name-only
    // selection so older firmware cannot silently choose a different image.
    prefs.remove("image");
    strlcpy(selected_image,name,sizeof(selected_image));memcpy(selected_digest,digest,32);
    strlcpy(state.image,name,sizeof(state.image));return true;
}
bool start_deploy(int i,const char* name,const uint8_t* expected) {
    if(!ready||!state.radio||state.busy||upload||sd_relay.pending||i<0||i>=16||!state.nodes[i].registered||!state.nodes[i].observed||health_at(state.nodes[i],millis())==Health::Stale||health_at(state.nodes[i],millis())==Health::Offline||state.nodes[i].receiver!=1||!valid_image_name(name))return false;
    transfer.file=SD.open(image_path(name),FILE_READ);
    if(!inspect_image(transfer.file,transfer.file_sha,transfer.image_sha)||!equal(expected,transfer.image_sha,32)){transfer.file.close();return false;}
    transfer.previous_boots=state.nodes[i].boots;transfer.node=i;transfer.offset=0;transfer.total=transfer.file.size();esp_fill_random(transfer.nonce,16);transfer.stage=Deployment::Opening;
    state.busy=true;state.offset=0;state.total=transfer.total;state.nodes[i].deployment_verified=false;
    char label[3];label_for(i,label);snprintf(state.deployment,sizeof(state.deployment),"Deploying to %s",label);
    send_stage(Kind::Open,nullptr,0,0);return true;
}
void next_mission_node(){
    auto& d=mission_dispatch;
    while(++d.node<16){
        const auto& n=state.nodes[d.node];
        if(!n.registered||!n.mission_capable||(d.start&&(health_at(n,millis())==Health::Stale||health_at(n,millis())==Health::Offline||!n.observed))){state.mission_failed|=1u<<d.node;continue;}
        if(d.start&&int32_t(d.deadline-millis())<500){state.mission_failed|=1u<<d.node;continue;}
        d.command=state.mission;if(!d.start&&n.mission_run)d.command.run=n.mission_run;
        d.opening=true;esp_fill_random(d.nonce,16);mission_send(Kind::Open,nullptr,0,0);return;
    }
    d.active=false;state.busy=false;
    snprintf(state.mission_status,sizeof(state.mission_status),"%s / %u accepted, %u failed",d.start?"Launch sent":"Stop sent",unsigned(__builtin_popcount(state.mission_accepted)),unsigned(__builtin_popcount(state.mission_failed)));
}
bool start_mission(const recon::Config& requested,bool start){
    if(!ready||!state.radio||state.busy||upload||sd_relay.pending)return false;
    auto config=requested;
    if(!config.run){config.run=esp_random();if(!config.run)config.run=1;}
    if(!config.seed){config.seed=esp_random();if(!config.seed)config.seed=1;}
    if(!recon::valid(config))return false;
    state.mission=config;state.mission_requested=start;state.mission_accepted=state.mission_failed=0;
    mission_dispatch={};mission_dispatch.active=true;mission_dispatch.start=start;mission_dispatch.deadline=millis()+12000;
    state.busy=true;strlcpy(state.mission_status,start?"Sending launch / awaiting node reports":"Sending stop / awaiting node reports",sizeof(state.mission_status));next_mission_node();return true;
}
void handle(Packet& packet) {
    int i=-1;for(int n=0;n<16;++n)if(state.nodes[n].registered&&equal(packet.source,bindings[n].mac,6)){i=n;break;}if(i<0)return;
    View v{};if(!authenticate(packet.bytes,packet.size,bindings[i].key,v)||!equal(v.sender,packet.source,6)||!equal(v.target,own,6))return;
    Binding& b=bindings[i];Node& n=state.nodes[i];
    if(v.kind==Kind::SdReply){
        if(sd_relay.pending&&i==sd_relay.node&&v.sequence==sd_relay.sequence&&equal(v.nonce,sd_relay.nonce,16)&&flocksd::report_valid(v.payload,v.length)){
            memcpy(sd_relay.report,v.payload,flocksd::ReportSize);sd_relay.pending=false;sd_relay.complete=true;
        }
        return;
    }
    if(v.kind==Kind::Health) {
        if((v.length!=HealthSize&&v.length!=recon::HealthSize)||!expected_health(b.pending,millis(),b.pending_at,v.sequence,b.sequence,v.nonce,b.nonce)||v.payload[0]!='A'+i/4||v.payload[1]!='1'+i%4)return;
        b.pending=false;n.observed=true;n.last_seen_ms=millis();n.health=v.payload[2]?Health::Healthy:Health::Warning;n.receiver=v.payload[3];memcpy(n.version,v.payload+4,16);n.version[16]=0;char observed_image[65];hex(v.payload+20,32,observed_image);if(strcmp(n.image,observed_image))n.deployment_verified=false;strlcpy(n.image,observed_image,sizeof(n.image));n.boots=get32(v.payload+52);n.ota_state=v.payload[60];n.sd=v.payload[75];n.sensors=v.payload[84];n.audio=v.payload[85];
        n.mission_overview=v.length==recon::HealthSize ? recon::decode_overview(v.payload[116],v.payload[117]) : recon::Overview::Unknown;
        n.mission_capable=v.length==recon::HealthSize&&v.payload[96]==1&&v.payload[98]<recon::Count&&v.payload[99]<5;
        if(n.mission_capable){n.mission_running=v.payload[97]&1;n.mission_waiting=v.payload[97]&2;n.mission_state=v.payload[98];n.mission_sensor=v.payload[99];n.mission_run=get32(v.payload+100);n.mission_elapsed=get32(v.payload+104);n.mission_cycle=get32(v.payload+108);n.mission_scenario=v.payload[112];n.mission_goal=v.payload[113];}
        else {n.mission_running=false;n.mission_waiting=false;n.mission_run=0;n.mission_state=recon::READY;}
        if(transfer.stage==Deployment::Verifying&&i==transfer.node&&valid_deployment_boot(transfer.previous_boots,n.boots,n.ota_state,n.receiver,v.payload[2],v.payload+20,transfer.image_sha)) {n.deployment_verified=true;transfer.stage=Deployment::Idle;state.busy=false;snprintf(state.deployment,sizeof(state.deployment),"Verified: expected image booted valid");}
        return;
    }
    auto& d=mission_dispatch;
    if(d.active&&i==d.node&&equal(v.nonce,d.nonce,16)&&v.sequence==uint32_t(d.opening?0:1)){
        if(d.opening&&v.kind==Kind::Challenge&&v.length==16){
            memcpy(d.nonce,v.payload,16);d.opening=false;uint8_t body[recon::CommandSize];
            if(d.start&&int32_t(d.deadline-millis())<500){state.mission_failed|=1u<<i;next_mission_node();return;}
            recon::command_encode(body,d.command,d.start,d.start?d.deadline-millis():0);mission_send(Kind::Mission,body,sizeof(body),1);return;
        }
        if(v.kind==Kind::MissionReply&&v.length==5&&get32(v.payload+1)==d.command.run){if(v.payload[0]==uint8_t(Code::Ok))state.mission_accepted|=1u<<i;else state.mission_failed|=1u<<i;next_mission_node();return;}
        if(v.kind==Kind::Ack&&v.length==5&&v.payload[0]!=0){state.mission_failed|=1u<<i;next_mission_node();return;}
    }
    if(i!=transfer.node||transfer.stage==Deployment::Idle||!equal(v.nonce,transfer.nonce,16)||v.sequence!=transfer.sequence)return;
    if(transfer.stage==Deployment::Opening&&v.kind==Kind::Challenge&&v.length==16){memcpy(transfer.nonce,v.payload,16);uint8_t body[73];put32(body,transfer.total);memcpy(body+4,transfer.file_sha,32);memcpy(body+36,transfer.image_sha,32);memcpy(body+68,"WS32",4);body[72]=1;transfer.stage=Deployment::Beginning;send_stage(Kind::Begin,body,sizeof(body),1);return;}
    if(v.kind!=Kind::Ack||v.length!=5)return;
    uint32_t offset=get32(v.payload+1);
    if(v.payload[0]!=uint8_t(Code::Ok)){fail("receiver rejected transfer");return;}
    if(transfer.stage==Deployment::Beginning){if(offset!=0){fail("BEGIN offset");return;}next_data();}
    else if(transfer.stage==Deployment::Sending){View sent{};decode(transfer.frame.bytes,transfer.frame.size,sent);uint32_t expected=transfer.offset+sent.length-4;if(offset!=expected){fail("DATA offset");return;}transfer.offset=offset;state.offset=offset;next_data();}
    else if(transfer.stage==Deployment::Committing){if(offset!=transfer.total){fail("COMMIT offset");return;}transfer.file.close();transfer.stage=Deployment::Verifying;transfer.verify_started=millis();snprintf(state.deployment,sizeof(state.deployment),"Transfer complete / awaiting valid boot");}
}
void tick() {
    uint32_t now=millis();state.wifi=WiFi.status()==WL_CONNECTED;strlcpy(state.ip,state.wifi?WiFi.localIP().toString().c_str():"",sizeof(state.ip));
    if(transfer.stage!=Deployment::Idle&&transfer.stage!=Deployment::Verifying&&now-transfer.sent>=500) {
        if(reply_timed_out(transfer.stage==Deployment::Beginning,now,transfer.wait_started)){
            if(transfer.stage==Deployment::Committing){transfer.file.close();transfer.stage=Deployment::Verifying;transfer.verify_started=now;strlcpy(state.deployment,"Commit ACK lost / checking boot",sizeof(state.deployment));}
            else fail("radio response timeout");
        }
        else{esp_now_send(bindings[transfer.node].mac,transfer.frame.bytes,transfer.frame.size);++transfer.tries;++transfer_retries;transfer.sent=now;}
    }
    if(transfer.stage==Deployment::Verifying&&now-transfer.verify_started>90000)fail("boot not verified in 90 seconds");
    for(int i=0;i<16;++i)if(!state.nodes[i].observed||now-state.nodes[i].last_seen_ms>=30000)state.nodes[i].deployment_verified=false;
    // Pace polls even after startup or a busy worker interval; never burst all 16.
    static uint32_t last_health_send=0;
    static uint8_t next_health_node=0;
    if(now-last_health_send>=kHealthPollMs/16){
        for(int offset=0;offset<16;++offset){int i=(next_health_node+offset)%16;
            if(!state.nodes[i].registered||now-bindings[i].poll_at<kHealthPollMs)continue;
            Binding& b=bindings[i];b.poll_at=now;b.pending_at=now;b.retry_at=now;b.retries=0;b.pending=true;++b.sequence;esp_fill_random(b.nonce,16);
            Frame f;encode(f,Kind::Poll,own,b.mac,b.nonce,b.sequence,nullptr,0);emit(f,i);
            next_health_node=(i+1)%16;last_health_send=now;break;
        }
    }
    static uint32_t last_health_retry=0;
    if(now-last_health_retry>=40){
        for(int i=0;i<16;++i){auto& b=bindings[i];
            if(!state.nodes[i].registered||!health_retry_due(b.pending,b.retries,now,b.pending_at,b.retry_at))continue;
            Frame f;encode(f,Kind::Poll,own,b.mac,b.nonce,b.sequence,nullptr,0);emit(f,i);
            b.retry_at=now;++b.retries;++health_poll_retries;last_health_retry=now;break;
        }
    }
    if(sd_relay.pending&&now-sd_relay.sent>=500){
        if(now-sd_relay.started>=6000){sd_relay.pending=false;sd_relay.timed_out=true;}
        else{emit(sd_relay.frame,sd_relay.node);sd_relay.sent=now;}
    }
    if(mission_dispatch.active&&now-mission_dispatch.sent>=250){
        auto& d=mission_dispatch;
        if(now-d.began>=2000){state.mission_failed|=1u<<d.node;next_mission_node();}
        else{emit(d.frame,d.node);d.sent=now;}
    }
    if(upload&&now-upload_last>30000){upload.close();SD.remove(upload_path);}
}
void status(JsonDocument& out) {
    out["upload_status_supported"]=true;
    out["type"]="console_status";out["boot_id"]=boot_id;out["uptime_ms"]=millis();out["free_internal"]=heap_caps_get_free_size(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);out["largest_internal"]=heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL|MALLOC_CAP_8BIT);out["serial_write_failures"]=serial_write_failures;out["transfer_retries"]=transfer_retries;out["rx_queue_overflows"]=rx_queue_overflows.load();out["version"]=kVersion;out["radio"]=state.radio;out["wifi_connected"]=state.wifi;out["ip"]=state.ip;out["channel"]=WiFi.channel();out["sd_mounted"]=sd_ready;
    char selected_hash[65]{};if(selected_image[0])hex(selected_digest,32,selected_hash);out["image_sha256"]=selected_hash;out["image"]=selected_image;out["deployment"]=state.deployment;out["busy"]=state.busy;out["offset"]=state.offset;out["total"]=state.total;
    out["health_poll_retries"]=health_poll_retries;out["mission_run"]=state.mission.run;out["mission_requested"]=state.mission_requested;out["mission_scenario"]=state.mission.scenario;out["mission_goal"]=state.mission.goal;out["mission_status"]=state.mission_status;out["mission_accepted"]=state.mission_accepted;out["mission_failed"]=state.mission_failed;
    JsonArray nodes=out["nodes"].to<JsonArray>();for(int i=0;i<16;++i){const Node& n=state.nodes[i];auto o=nodes.add<JsonObject>();char label[3];label_for(i,label);o["label"]=label;o["registered"]=n.registered;o["mac"]=n.mac;o["observed"]=n.observed;o["health"]=health_name(health_at(n,millis()));o["age_ms"]=n.observed?millis()-n.last_seen_ms:0;o["version"]=n.version;o["image_sha256"]=n.image;o["receiver_version"]=n.receiver;o["ota_state"]=n.ota_state;o["deployment_verified"]=n.deployment_verified;o["boots"]=n.boots;o["sd_pass"]=n.sd;o["sensor_bits"]=n.sensors;o["audio_bits"]=n.audio;o["mission_capable"]=n.mission_capable;o["mission_run"]=n.mission_run;o["mission_running"]=n.mission_running;o["mission_waiting"]=n.mission_waiting;o["mission_state"]=recon::name(n.mission_state);o["mission_overview"]=recon::overview_name(n.mission_overview);o["overview_label"]=overview_label(n,millis());o["mission_elapsed_ms"]=n.mission_elapsed;o["mission_cycle"]=n.mission_cycle;}
}
void command(const char* line) {
    JsonDocument in,out;auto err=deserializeJson(in,line);const char* id=in["id"]|"";out["v"]=1;out["id"]=id;out["request_id"]=id;out["base_mac"]=own_text;out["ok"]=false;
    auto error=[&](const char* s){out["error"]=s;};
    if(err||in["v"].as<int>()!=1||!id[0]||strlen(id)>96)error("invalid_request");
    else if(strcmp(in["target"]|"",own_text)||strcmp(own_text,ExpectedMac))error("wrong_target");
    else {
        const char* op=in["op"]|"";bool ok=false;
        if(!strcmp(op,"status")){status(out);ok=true;}
        else if(!strcmp(op,"mission_start")||!strcmp(op,"mission_stop")){
            recon::Config config;bool valid=true;
            for(const char*k:{"scenario","goal","seconds","run","seed"})if(!in[k].isNull()&&!in[k].is<uint32_t>())valid=false;
            if(!in["repeat"].isNull()&&!in["repeat"].is<bool>())valid=false;
            uint32_t scenario=in["scenario"]|0u,goal=in["goal"]|0u,seconds=in["seconds"]|64u;
            config.scenario=scenario;config.goal=goal;config.seconds=seconds;config.run=in["run"]|0u;config.seed=in["seed"]|0u;config.repeat=in["repeat"]|true;
            if(!valid||scenario>2||goal>2||(seconds!=64&&seconds!=96)||!start_mission(config,!strcmp(op,"mission_start")))error("mission_unavailable");else{out["run"]=state.mission.run;ok=true;}
        }
        else if(!strcmp(op,"wifi")){
            const char* ssid=in["ssid"]|"";const char* password=in["password"]|"";
            if(state.busy||upload)error("busy");
            else if(!ssid[0]||strlen(ssid)>32||strlen(password)>63)error("invalid_wifi");
            else {WiFi.begin(ssid,password);ok=true;}
        } else if(!strcmp(op,"register")) {
            const char* label=in["label"]|"";int i=strlen(label)==2?label_index(label[0],label[1]):-1;uint8_t mac[6],key[32];
            if(i<0||!mac_parse(in["mac"]|"",mac)||!unhex(in["key"]|"",key,32))error("invalid_binding");
            else if(state.busy||upload)error("busy");
            else {
                bool conflict=false;for(int j=0;j<16;++j)if(state.nodes[j].registered){if(j!=i&&equal(bindings[j].mac,mac,6))conflict=true;if(j==i&&(!equal(bindings[j].mac,mac,6)||!equal(bindings[j].key,key,32)))conflict=true;}
                if(conflict)error("binding_conflict");else {uint8_t record[38];memcpy(record,mac,6);memcpy(record+6,key,32);if(prefs.putBytes(label,record,sizeof(record))!=sizeof(record)||!add_peer(mac))error("binding_store_failed");else{memcpy(bindings[i].mac,mac,6);memcpy(bindings[i].key,key,32);state.nodes[i].registered=true;bindings[i].poll_at=millis()-kHealthPollMs;mac_text(mac,state.nodes[i].mac);ok=true;}}
            }
        } else if(!strcmp(op,"image_begin")) {
            const char* name=in["name"]|"";uint32_t size=in["size"]|0;
            if(state.busy||upload)error("busy");else if(!sd_ready||!valid_image_name(name)||size<288||size>MaxImage||!unhex(in["sha256"]|"",upload_sha,32))error("invalid_image");
            else if(SD.exists(image_path(name)))error("image_exists");
            else {SD.mkdir("/flockinator");SD.mkdir("/flockinator/images");uint8_t random[16];char suffix[33];esp_fill_random(random,sizeof(random));hex(random,sizeof(random),suffix);snprintf(upload_path,sizeof(upload_path),"/flockinator/images/.upload-%s.tmp",suffix);upload=SD.exists(upload_path)?File():SD.open(upload_path,FILE_WRITE);if(!upload)error("sd_create_failed");else{upload_size=size;upload_offset=0;upload_last=millis();strlcpy(upload_name,name,sizeof(upload_name));ok=true;}}
        } else if(!strcmp(op,"image_status")) {
            out["boot_id"]=boot_id;out["active"]=bool(upload);
            if(upload){char hash[65];hex(upload_sha,32,hash);out["name"]=upload_name;out["size"]=upload_size;out["sha256"]=hash;out["offset"]=upload_offset;upload_last=millis();}
            ok=true;
        } else if(!strcmp(op,"image_chunk")) {
            const char* data=in["data"]|"";size_t n=strlen(data)/2;uint8_t bytes[512];uint32_t offset=in["offset"]|UINT32_MAX;
            if(!upload||!n||n>512||!unhex(data,bytes,n)||offset!=upload_offset||n>upload_size-upload_offset)error("invalid_chunk");
            else if(upload.write(bytes,n)!=n){upload.close();SD.remove(upload_path);error("sd_write_failed");}
            else {upload_offset+=n;upload_last=millis();out["offset"]=upload_offset;ok=true;}
        } else if(!strcmp(op,"image_end")) {
            if(!upload||upload_offset!=upload_size)error("image_incomplete");
            else{upload.flush();upload.close();File file=SD.open(upload_path,FILE_READ);uint8_t hash[32],digest[32];bool valid=inspect_image(file,hash,digest)&&equal(hash,upload_sha,32);file.close();
                if(!valid){SD.remove(upload_path);error("image_validation_failed");}
                else if(SD.exists(image_path(upload_name))||!SD.rename(upload_path,image_path(upload_name)))error("image_publish_failed");
                else if(!persist_selection(upload_name,digest))error("selection_store_failed");
                else {char imagehash[65];hex(digest,32,imagehash);out["image_sha256"]=imagehash;ok=true;}
            }
        } else if(!strcmp(op,"image_select")) {
            const char* name=in["name"]|"";
            if(state.busy||upload)error("busy");
            else if(!may_select_image(sd_ready,state.busy,bool(upload),name))error("invalid_image");
            else {File file=SD.open(image_path(name),FILE_READ);uint8_t full[32],digest[32];bool valid=inspect_image(file,full,digest);file.close();
                if(!valid)error("image_validation_failed");
                else if(!persist_selection(name,digest))error("selection_store_failed");
                else {char hash[65];hex(digest,32,hash);out["image"]=name;out["image_sha256"]=hash;hex(full,32,hash);out["file_sha256"]=hash;ok=true;}
            }
        } else if(!strcmp(op,"sd_request")) {
            const char* label=in["label"]|"";int i=strlen(label)==2?label_index(label[0],label[1]):-1;
            int action=in["action"]|-1;uint8_t body[57]{};size_t length=action<2?1:57;
            if(state.busy||upload||sd_relay.pending)error("busy");
            else if(!ready||!state.radio||i<0||!state.nodes[i].registered||action<0||action>3)error("invalid_sd_request");
            else if(action>=2&&(!unhex(in["card_id"]|"",body+1,40)||!unhex(in["token"]|"",body+41,16)))error("invalid_card_permit");
            else{
                body[0]=action;sd_relay.node=i;sd_relay.pending=true;sd_relay.complete=sd_relay.timed_out=false;
                ++sd_relay.sequence;esp_fill_random(sd_relay.nonce,16);sd_relay.started=sd_relay.sent=millis();
                encode(sd_relay.frame,Kind::SdRequest,own,bindings[i].mac,sd_relay.nonce,sd_relay.sequence,body,length);emit(sd_relay.frame,i);
                char correlation[33];hex(sd_relay.nonce,16,correlation);out["transaction"]=correlation;out["node_mac"]=state.nodes[i].mac;ok=true;
            }
        } else if(!strcmp(op,"sd_result")) {
            uint8_t correlation[16];
            if(!unhex(in["transaction"]|"",correlation,16)||!equal(correlation,sd_relay.nonce,16)||sd_relay.node<0)error("unknown_sd_transaction");
            else{
                out["pending"]=sd_relay.pending;out["complete"]=sd_relay.complete;out["timed_out"]=sd_relay.timed_out;
                out["node_mac"]=state.nodes[sd_relay.node].mac;
                if(sd_relay.complete){char report[flocksd::ReportSize*2+1];hex(sd_relay.report,flocksd::ReportSize,report);out["report_hex"]=report;}
                ok=true;
            }
        } else if(!strcmp(op,"deploy")) {
            const char* label=in["label"]|"";int i=strlen(label)==2?label_index(label[0],label[1]):-1;uint8_t digest[32];
            if(!unhex(in["image_sha256"]|"",digest,32)||!start_deploy(i,in["name"]|"",digest))error("deployment_unavailable");else ok=true;
        } else error("unknown_operation");
        out["ok"]=ok;
    }
    String response;response.reserve(8192);size_t encoded=serializeJson(out,response);if(out.overflowed()||encoded!=measureJson(out)){++serial_write_failures;return;}response += '\n';
    if(response.length()>kSerialReplyMax){++serial_write_failures;return;}
    // One driver call holds the TX lock for the entire JSON line. Byte-at-a-time
    // Print serialization can lose/interleave bytes with the pinned HWCDC driver.
    size_t written=Serial.write(reinterpret_cast<const uint8_t*>(response.c_str()),response.length());
    if(written!=response.length())++serial_write_failures;
}
void worker(void*) {
    Serial.printf("live:worker_running\n");
    char line[2048];size_t used=0;bool overflow=false;
    for(;;) {
        lock();if(paused){unlock();vTaskDelay(pdMS_TO_TICKS(20));continue;}Packet packet;for(int n=0;n<8&&xQueueReceive(queue,&packet,0)==pdTRUE;++n)handle(packet);if(state.radio)tick();
        size_t serial_budget=2048;
        while(serial_budget-- && Serial.available()) {char c=Serial.read();if(c=='\n'){if(!overflow&&used){line[used]=0;command(line);}used=0;overflow=false;}else if(c!='\r'){if(used<sizeof(line)-1&&!overflow)line[used++]=c;else{used=0;overflow=true;}}}
        unlock();vTaskDelay(pdMS_TO_TICKS(5));
    }
}
}
void live_begin() {
    Serial.printf("live:init\n");
    sd_ready=diagnostics().sd;
    uint8_t boot_nonce[16];esp_fill_random(boot_nonce,16);hex(boot_nonce,16,boot_id);
    mutex=xSemaphoreCreateMutex();queue=xQueueCreate(12,sizeof(Packet));esp_read_mac(own,ESP_MAC_WIFI_STA);mac_text(own,own_text);
    for(int i=0;i<16;++i){state.nodes[i].id=i+1;state.nodes[i].health=Health::Unknown;bindings[i].poll_at=millis()-kHealthPollMs;}
    Serial.printf("live:nvs\n");
    ready=mutex&&queue&&prefs.begin("flock-live",false)&&!strcmp(own_text,ExpectedMac);
    Serial.printf("live:identity_ready=%d\n",ready);
    if(!ready){strlcpy(state.deployment,"Identity or storage unavailable",sizeof(state.deployment));return;}
    WiFi.persistent(true);Serial.printf("live:wifi_mode\n");WiFi.mode(WIFI_STA);Serial.printf("live:wifi_sleep\n");WiFi.setSleep(false);Serial.printf("live:wifi_begin\n");WiFi.begin();Serial.printf("live:wifi_begin_done\n");
    Serial.printf("live:espnow_init\n");
    if(esp_now_init()==ESP_OK&&esp_now_register_recv_cb(receive)==ESP_OK)state.radio=true;
    Serial.printf("live:radio=%d roster_load\n",state.radio);
    for(int i=0;i<16;++i){char label[3];label_for(i,label);uint8_t record[38];if(prefs.getBytesLength(label)==sizeof(record)&&prefs.getBytes(label,record,sizeof(record))==sizeof(record)){memcpy(bindings[i].mac,record,6);memcpy(bindings[i].key,record+6,32);state.nodes[i].registered=add_peer(record);mac_text(record,state.nodes[i].mac);}}
    Serial.printf("live:image_load\n");
    uint8_t saved[97]{};bool have_selection=prefs.getBytesLength("selection")==sizeof(saved)&&prefs.getBytes("selection",saved,sizeof(saved))==sizeof(saved);
    saved[64]=0;
    String image=have_selection?String(reinterpret_cast<char*>(saved)):prefs.getString("image","");
    if(sd_ready&&valid_image_name(image.c_str())){File f=SD.open(image_path(image.c_str()),FILE_READ);uint8_t sha[32],digest[32];if(inspect_image(f,sha,digest)&&(!have_selection||equal(digest,saved+65,32))){strlcpy(selected_image,image.c_str(),sizeof(selected_image));memcpy(selected_digest,digest,32);strlcpy(state.image,selected_image,sizeof(state.image));}f.close();}

    Serial.printf("live:worker_start\n");
    if(xTaskCreatePinnedToCore(worker,"flock-live",12288,nullptr,2,nullptr,0)!=pdPASS){ready=false;strlcpy(state.deployment,"Radio worker allocation failed",sizeof(state.deployment));Serial.printf("console_worker=failed\n");}
    Serial.printf("live:begin_done\n");
}
LiveSnapshot live_snapshot(){if(!mutex)return state;lock();LiveSnapshot copy=state;unlock();return copy;}
bool live_deploy_selected(int index){if(!ready)return false;lock();bool ok=start_deploy(index,selected_image,selected_digest);if(!ok)strlcpy(state.deployment,"Cannot deploy: check node, radio and stored image",sizeof(state.deployment));unlock();return ok;}
bool live_mission(const recon::Config& config,bool start){if(!ready)return false;lock();bool ok=start_mission(config,start);if(!ok)strlcpy(state.mission_status,"Unavailable / finish current transfer first",sizeof(state.mission_status));unlock();return ok;}
bool live_pause(bool value){if(!mutex)return true;lock();if(value&&(state.busy||upload||sd_relay.pending)){unlock();return false;}paused=value;unlock();return true;}
bool live_can_sleep(){if(!ready)return true;lock();bool allowed=!state.busy&&!upload&&!sd_relay.pending;unlock();return allowed;}
}
