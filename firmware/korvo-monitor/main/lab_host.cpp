#include "lab_host.h"
#include "controller.h"
#include "lab_model.h"
#include <cstdio>
#include <cstring>
#include <cctype>
#include <cinttypes>
#include <string>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_random.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_netif_sntp.h"
#include "nvs_flash.h"
#include "psa/crypto.h"

namespace {
using namespace signals;
Model model;
SemaphoreHandle_t guard;
nvs_handle_t store;
esp_netif_t* station;
httpd_handle_t server;
struct Saved {uint32_t schema,seed,id,revision,turn,link,paused;};
Saved run{};
char ip[16]="";
bool online=false,configured=false;
TaskHandle_t ticker;
class Lock {public: Lock(){xSemaphoreTake(guard,portMAX_DELAY);} ~Lock(){xSemaphoreGive(guard);}};
bool hash(const char* text,unsigned char output[64]){
    size_t length=0;
    return psa_hash_compute(PSA_ALG_SHA_512,(const uint8_t*)text,strlen(text),output,64,&length)==PSA_SUCCESS&&length==64;
}
bool persist(const Saved& s){return nvs_set_blob(store,"world",&s,sizeof(s))==ESP_OK && nvs_commit(store)==ESP_OK;}
Saved fresh(uint32_t seed,uint32_t link){return {1,seed,esp_random()|1u,esp_random(),0,link,0};}
void tick(void*){
    for(;;){
        vTaskDelay(pdMS_TO_TICKS(500));
        Lock lock;
        if(run.paused || model.turn>=Train+Test)continue;
        model.step();run.turn=model.turn;
        if(model.turn%8==0 && !persist(run))ESP_LOGE("lab","World checkpoint write failed");
    }
}
extern "C" const char lab_page[] asm("_binary_lab_html_start");
extern "C" const char lab_script[] asm("_binary_lab_js_start");
extern "C" const char lab_css[] asm("_binary_lab_css_start");
esp_err_t asset(httpd_req_t* r){
    const bool js=!strcmp(r->uri,"/lab.js"), css=!strcmp(r->uri,"/lab.css");
    httpd_resp_set_type(r,js?"text/javascript":css?"text/css":"text/html");
    httpd_resp_set_hdr(r,"Cache-Control","no-store");
    httpd_resp_set_hdr(r,"Content-Security-Policy","default-src 'self'; frame-ancestors 'none'");
    return httpd_resp_sendstr(r,js?lab_script:css?lab_css:lab_page);
}
esp_err_t json(httpd_req_t* r,const char* body){
    httpd_resp_set_type(r,"application/json");httpd_resp_set_hdr(r,"Cache-Control","no-store");
    return httpd_resp_sendstr(r,body);
}
esp_err_t state(httpd_req_t* r){
    char body[1024];
    {
        Lock lock;
        char scores[200];int length=0;
        for(int a=0;a<5;a++){
            auto& s=a==4?model.solo:model.scores[a];
            length+=snprintf(scores+length,sizeof(scores)-length,"%s[%d,%d,%d]",a?",":"",s.recovered,s.correct,s.packets);
        }
        snprintf(body,sizeof(body),"{\"engine\":\"field-signals-v1\",\"host\":\"Korvo ESP32-S31\",\"run\":%lu,\"revision\":%lu,\"seed\":%lu,\"turn\":%d,\"link\":%lu,\"paused\":%s,\"scores\":[%s],\"known\":[%d,%d],\"accurate\":[%d,%d],\"training_packets\":[%d,%d]}",
            (unsigned long)run.id,(unsigned long)run.revision,(unsigned long)run.seed,model.turn,(unsigned long)run.link,run.paused?"true":"false",
            scores,model.known[0],model.known[1],model.mappings[0],model.mappings[1],model.training_packets[0],model.training_packets[1]);
    }
    return json(r,body);
}
esp_err_t round_view(httpd_req_t* r){
    char query[80],extra;
    unsigned long id;int round;
    if(httpd_req_get_url_query_str(r,query,sizeof(query))!=ESP_OK ||
       sscanf(query,"run=%lu&round=%d%c",&id,&round,&extra)!=2 || round<1 || round>Test)
        return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid round");
    std::string body;body.reserve(2300);
    {
        Lock lock;
        if(run.id!=id || round>model.turn-Train)return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Round unavailable");
        body="{\"units\":[";
        auto& w=model.held[round-1];
        for(int i=0;i<Units;i++){
            auto a=model.choose(w,i,0,Clear),b=model.choose(w,i,0,model.intervention);
            char line[160];snprintf(line,sizeof(line),"%s{\"cue\":%u,\"truth\":%u,\"clear\":[%u,%u,%u,%u,%u,%u,%u],\"altered\":[%u,%u,%u,%u,%u,%u,%u]}",
                i?",":"",w.cue[i],w.truth[i/4],a.sector,a.token[0],a.decoded[0],a.token[1],a.decoded[1],a.token[2],a.decoded[2],
                b.sector,b.token[0],b.decoded[0],b.token[1],b.decoded[1],b.token[2],b.decoded[2]);body+=line;
        }
        body+="]}";
    }
    return json(r,body.c_str());
}
bool local_request(httpd_req_t* r){
    char host[64],origin[96],type[64],here[16];
    {Lock lock;snprintf(here,sizeof(here),"%s",ip);}
    if(httpd_req_get_hdr_value_str(r,"Host",host,sizeof(host))!=ESP_OK || strcmp(host,here))return false;
    if(httpd_req_get_hdr_value_str(r,"Content-Type",type,sizeof(type))!=ESP_OK || strcmp(type,"application/x-flock-lab"))return false;
    if(httpd_req_get_hdr_value_len(r,"Origin")){
        char expected[80];snprintf(expected,sizeof(expected),"http://%s",host);
        if(httpd_req_get_hdr_value_str(r,"Origin",origin,sizeof(origin))!=ESP_OK || strcmp(origin,expected))return false;
    }
    return true;
}
esp_err_t control(httpd_req_t* r){
    if(!local_request(r))return httpd_resp_send_err(r,HTTPD_403_FORBIDDEN,"Direct controller origin required");
    char text[96]{},op[8]{},extra;
    if(!r->content_len || r->content_len>=sizeof(text))return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid command");
    size_t n=0;
    while(n<r->content_len){int k=httpd_req_recv(r,text+n,r->content_len-n);if(k<=0)return ESP_FAIL;n+=k;}
    unsigned long rev,seed,link;
    if(sscanf(text,"%7[a-z] %lu %lu %lu%c",op,&rev,&seed,&link,&extra)!=4 || link<1 || link>3 ||
       strspn(text,"abcdefghijklmnopqrstuvwxyz 0123456789")!=n)
        return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid settings");
    {
        Lock lock;
        if(rev!=run.revision){httpd_resp_set_status(r,"409 Conflict");return json(r,"{\"error\":\"World changed. Refresh and retry.\"}");}
        Saved next=run;
        if(!strcmp(op,"start"))next=fresh(seed,link);
        else if(!strcmp(op,"pause")&&!run.paused&&model.turn<Train+Test)next.paused=1;
        else if(!strcmp(op,"resume")&&run.paused)next.paused=0;
        else return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid transition");
        next.revision=run.revision+1;
        if(!persist(next))return httpd_resp_send_err(r,HTTPD_500_INTERNAL_SERVER_ERROR,"World save failed");
        if(!strcmp(op,"start") && !model.init(next.seed,Link(next.link),hash))return ESP_FAIL;
        run=next;
    }
    return state(r);
}
void web(){
    if(server)return;
    httpd_config_t cfg=HTTPD_DEFAULT_CONFIG();cfg.stack_size=24576;cfg.lru_purge_enable=true;cfg.max_uri_handlers=32;cfg.uri_match_fn=httpd_uri_match_wildcard;
    if(httpd_start(&server,&cfg)!=ESP_OK){ESP_LOGE("lab","HTTP startup failed");return;}
    for(const char* path:{"/lab","/lab.js","/lab.css","/api/state","/api/round","/api/control"}){
        httpd_uri_t ep{};ep.uri=path;ep.method=!strcmp(path,"/api/control")?HTTP_POST:HTTP_GET;
        ep.handler=!strcmp(path,"/api/control")?control:!strcmp(path,"/api/state")?state:!strcmp(path,"/api/round")?round_view:asset;
        ESP_ERROR_CHECK(httpd_register_uri_handler(server,&ep));
    }
    standalone_web(server);
}
void wifi_event(void*,esp_event_base_t base,int32_t event,void* data){
    if(base==IP_EVENT && event==IP_EVENT_STA_GOT_IP){
        auto* e=static_cast<ip_event_got_ip_t*>(data);
        {Lock lock;snprintf(ip,sizeof(ip),IPSTR,IP2STR(&e->ip_info.ip));online=true;}
        ESP_LOGI("lab","Controller URL http://" IPSTR "/",IP2STR(&e->ip_info.ip));
        standalone_network(true);esp_netif_sntp_start();web();
    }else if(base==WIFI_EVENT && event==WIFI_EVENT_STA_DISCONNECTED){
        standalone_network(false);
        {Lock lock;online=false;ip[0]=0;}
        esp_wifi_connect();
    }
}
bool decode(const char* str,uint8_t* out,size_t max,size_t* written){
    size_t n=strlen(str);if(!n || n%2 || n>max*2)return false;
    for(size_t i=0;i<n;i+=2){unsigned v;if(!isxdigit((unsigned char)str[i])||!isxdigit((unsigned char)str[i+1])||sscanf(str+i,"%2x",&v)!=1||!v)return false;out[i/2]=v;}
    *written=n/2;return true;
}
}
extern "C" void lab_start(){
    guard=xSemaphoreCreateMutex();if(!guard)return;
    if(nvs_flash_init()!=ESP_OK || nvs_open("flocklab",NVS_READWRITE,&store)!=ESP_OK || psa_crypto_init()!=PSA_SUCCESS){ESP_LOGE("lab","Initialization failed");return;}
    standalone_init();
    size_t size=sizeof(run);
    if(nvs_get_blob(store,"world",&run,&size)!=ESP_OK||size!=sizeof(run)||run.schema!=1||run.link<1||run.link>3||run.turn>Train+Test)
        run=fresh(11,Scrambled);
    if(!model.init(run.seed,Link(run.link),hash)){ESP_LOGE("lab","World initialization failed");return;}
    while(unsigned(model.turn)<run.turn)model.step();
    xTaskCreate(tick,"lab_world",8192,nullptr,2,&ticker);
    ESP_ERROR_CHECK(esp_netif_init());ESP_ERROR_CHECK(esp_event_loop_create_default());
    station=esp_netif_create_default_wifi_sta();esp_netif_set_hostname(station,"flockinator-korvo");
    esp_sntp_config_t time_config=ESP_NETIF_SNTP_DEFAULT_CONFIG("pool.ntp.org");
    time_config.start=false;
    ESP_ERROR_CHECK(esp_netif_sntp_init(&time_config));
    wifi_init_config_t cfg=WIFI_INIT_CONFIG_DEFAULT();ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT,WIFI_EVENT_STA_DISCONNECTED,wifi_event,nullptr));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT,IP_EVENT_STA_GOT_IP,wifi_event,nullptr));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    wifi_config_t w{};size=sizeof(w.sta);
    configured=nvs_get_blob(store,"wifi",&w.sta,&size)==ESP_OK && size==sizeof(w.sta);
    if(configured)ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA,&w));
    ESP_ERROR_CHECK(esp_wifi_start());if(configured)esp_wifi_connect();
}
extern "C" bool lab_provision(const char* text){
    char target[18],ssid[65],pass[127],extra;
    if(sscanf(text,"LW1 %17s %64s %126s%c",target,ssid,pass,&extra)!=3 || !station)return false;
    uint8_t mac[6];esp_read_mac(mac,ESP_MAC_BASE);char own[18];
    snprintf(own,sizeof(own),"%02X:%02X:%02X:%02X:%02X:%02X",mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
    wifi_config_t w{};size_t a,b;
    if(strcmp(own,target)||!decode(ssid,w.sta.ssid,sizeof(w.sta.ssid),&a)||!decode(pass,w.sta.password,63,&b)||b<8)return false;
    w.sta.threshold.authmode=WIFI_AUTH_WPA2_PSK;
    if(nvs_set_blob(store,"wifi",&w.sta,sizeof(w.sta))!=ESP_OK||nvs_commit(store)!=ESP_OK)return false;
    if(esp_wifi_set_config(WIFI_IF_STA,&w)!=ESP_OK)return false;
    configured=true;esp_wifi_connect();return true;
}
extern "C" void lab_metrics(lab_metrics_t* out){
    *out={};if(!guard)return;Lock lock;
    out->seed=run.seed;out->turn=model.turn;out->link=run.link;out->paused=run.paused;
    out->clear=model.scores[0].recovered;out->altered=model.scores[1].recovered;out->solo=model.solo.recovered;
    snprintf(out->ip,sizeof(out->ip),"%s",online?ip:"");
    if(model.turn>Train){
        auto& w=model.held[model.turn-Train-1];
        for(int i=0;i<Units;i++){
            bool a=model.choose(w,i,0,Clear).sector==w.truth[i/4],b=model.choose(w,i,0,model.intervention).sector==w.truth[i/4];
            out->correct[i]=a?(b?1:2):(b?3:4);
        }
    }
}
