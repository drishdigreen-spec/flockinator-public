#include "network.h"
#include "node_model.h"
#include "node_link.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include <cstring>
#include <cstdio>
static esp_netif_t* netif;
static bool wifi_ok=false,now_ok=false,configured=false,scan_ok=false;
static uint16_t ap_count=0;
static uint8_t own[6]{},broadcast[6]={255,255,255,255,255,255};
struct __attribute__((packed)) Probe { uint32_t magic; uint8_t version,kind; char label[2]; uint32_t seq; uint64_t nonce; };
struct Received { uint8_t source[6]; Probe packet; };
static_assert(sizeof(Probe)<=250);
static QueueHandle_t inbox;
static uint32_t seq=0,last_tx=0,last_reply=0,replies=0,sent=0,rtt=0;
static uint64_t nonce=0;
static char peer_label[3]="--",peer_mac[18]{};
static uint32_t reconnect_at=0,reconnect_delay=2000,reconnect_attempts=0;
static void receive(const esp_now_recv_info_t* info,const uint8_t* data,int len) {
    if(info && data && len>=4 && !memcmp(data,"FLK2",4)) { node_link_receive(info->src_addr,data,len); return; }
    if(!info || !data || len!=sizeof(Probe) || !inbox) return;
    Received r{}; memcpy(r.source,info->src_addr,6); memcpy(&r.packet,data,sizeof(Probe));
    if(r.packet.magic!=0x464c4b31 || r.packet.version!=1 || (r.packet.kind!=1 && r.packet.kind!=2)) return;
    char label[3]={r.packet.label[0],r.packet.label[1],0};
    if(!node::valid_label(label) || !memcmp(r.source,own,6)) return;
    xQueueSend(inbox,&r,0);
}
static bool add_peer(const uint8_t* mac) {
    if(esp_now_is_peer_exist(mac)) return true;
    esp_now_peer_info_t peer{}; memcpy(peer.peer_addr,mac,6); peer.channel=0; peer.ifidx=WIFI_IF_STA;
    return esp_now_add_peer(&peer)==ESP_OK;
}
void network_init() {
    if(nvs_flash_init()!=ESP_OK || esp_netif_init()!=ESP_OK) return;
    if(esp_event_loop_create_default()!=ESP_OK) return;
    netif=esp_netif_create_default_wifi_sta(); if(!netif) return;
    wifi_init_config_t cfg=WIFI_INIT_CONFIG_DEFAULT();
    wifi_ok=esp_wifi_init(&cfg)==ESP_OK && esp_wifi_set_mode(WIFI_MODE_STA)==ESP_OK && esp_wifi_start()==ESP_OK;
    if(!wifi_ok) return;
    esp_wifi_set_ps(WIFI_PS_NONE); esp_wifi_get_mac(WIFI_IF_STA,own);
    wifi_scan_config_t scan{}; scan.show_hidden=false;
    scan_ok=esp_wifi_scan_start(&scan,true)==ESP_OK && esp_wifi_scan_get_ap_num(&ap_count)==ESP_OK;
    esp_wifi_clear_ap_list();
    wifi_config_t stored{}; esp_wifi_get_config(WIFI_IF_STA,&stored); configured=stored.sta.ssid[0]!=0;
    if(configured) esp_wifi_connect(); else esp_wifi_set_channel(6,WIFI_SECOND_CHAN_NONE);
    inbox=xQueueCreate(8,sizeof(Received));
    now_ok=inbox && esp_now_init()==ESP_OK && esp_now_register_recv_cb(receive)==ESP_OK && add_peer(broadcast);
}
bool network_configure(const char* ssid,const char* password) {
    size_t sl=strlen(ssid),pl=strlen(password);
    if(!wifi_ok || sl<1 || sl>32 || pl<8 || pl>63) return false;
    wifi_config_t cfg{}; memcpy(cfg.sta.ssid,ssid,sl); memcpy(cfg.sta.password,password,pl);
    cfg.sta.threshold.authmode=WIFI_AUTH_WPA2_PSK; cfg.sta.pmf_cfg.capable=true;
    esp_wifi_disconnect();
    bool ok=esp_wifi_set_config(WIFI_IF_STA,&cfg)==ESP_OK; memset(&cfg,0,sizeof(cfg));
    configured=ok; return ok && esp_wifi_connect()==ESP_OK;
}
void network_tick(const char* label) {
    uint32_t now=esp_timer_get_time()/1000;
    if(configured && wifi_ok) {
        if(network_connected()) { reconnect_delay=2000; reconnect_at=now+reconnect_delay; }
        else if(static_cast<int32_t>(now-reconnect_at)>=0) {
            esp_wifi_connect(); ++reconnect_attempts;
            reconnect_at=now+reconnect_delay;
            reconnect_delay=reconnect_delay<30000?reconnect_delay*2:60000;
        }
    }
    if(!now_ok || !node::valid_label(label)) return;
    Received r{};
    for(int n=0;n<4 && xQueueReceive(inbox,&r,0)==pdTRUE;n++) {
        if(r.packet.kind==1 && add_peer(r.source)) {
            Probe reply=r.packet; reply.kind=2; memcpy(reply.label,label,2);
            esp_now_send(r.source,reinterpret_cast<uint8_t*>(&reply),sizeof(reply));
        } else if(r.packet.kind==2 && r.packet.seq==seq && r.packet.nonce==nonce && now-last_tx<5000) {
            last_reply=now; rtt=now-last_tx; replies++;
            memcpy(peer_label,r.packet.label,2);
            snprintf(peer_mac,sizeof(peer_mac),"%02X:%02X:%02X:%02X:%02X:%02X",r.source[0],r.source[1],r.source[2],r.source[3],r.source[4],r.source[5]);
        }
    }
    if(now-last_tx>=5000) {
        esp_fill_random(&nonce,sizeof(nonce)); ++seq;
        Probe request{0x464c4b31,1,1,{label[0],label[1]},seq,nonce};
        if(esp_now_send(broadcast,reinterpret_cast<uint8_t*>(&request),sizeof(request))==ESP_OK) sent++;
        last_tx=now;
    }
}
void network_json(cJSON* root) {
    auto* j=cJSON_AddObjectToObject(root,"network");
    char mac[18]; snprintf(mac,sizeof(mac),"%02X:%02X:%02X:%02X:%02X:%02X",own[0],own[1],own[2],own[3],own[4],own[5]);
    cJSON_AddStringToObject(j,"wifi_sta_mac",mac); cJSON_AddStringToObject(j,"espnow_mac",mac);
    cJSON_AddStringToObject(j,"wifi_radio",wifi_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"wifi_scan",scan_ok?"PASS":"FAIL"); cJSON_AddNumberToObject(j,"ap_count",ap_count);
    cJSON_AddBoolToObject(j,"wifi_configured",configured);
    wifi_ap_record_t ap{}; bool connected=wifi_ok && esp_wifi_sta_get_ap_info(&ap)==ESP_OK;
    cJSON_AddStringToObject(j,"association",connected?"PASS":"PENDING");
    if(connected) cJSON_AddNumberToObject(j,"rssi_dbm",ap.rssi);
    esp_netif_ip_info_t ip{}; bool has_ip=netif && esp_netif_get_ip_info(netif,&ip)==ESP_OK && ip.ip.addr;
    char address[16]; snprintf(address,sizeof(address),IPSTR,IP2STR(&ip.ip));
    cJSON_AddStringToObject(j,"ip",address); cJSON_AddStringToObject(j,"dhcp",has_ip?"PASS":"PENDING");
    uint8_t channel=0; wifi_second_chan_t second; if(wifi_ok) esp_wifi_get_channel(&channel,&second);
    cJSON_AddNumberToObject(j,"channel",channel);
    cJSON_AddNumberToObject(j,"reconnect_attempts",reconnect_attempts);
    cJSON_AddStringToObject(j,"espnow_init",now_ok?"PASS":"FAIL");
    uint32_t now=esp_timer_get_time()/1000;
    cJSON_AddStringToObject(j,"peer_roundtrip",last_reply?(now-last_reply<30000?"PASS":"STALE"):"PENDING");
    cJSON_AddStringToObject(j,"peer_label",peer_label); cJSON_AddStringToObject(j,"peer_mac",peer_mac);
    cJSON_AddNumberToObject(j,"probe_requests",sent); cJSON_AddNumberToObject(j,"replies",replies); cJSON_AddNumberToObject(j,"last_rtt_ms",rtt);
    cJSON_AddStringToObject(j,"remote_management","SEE_MAINTENANCE");
}

bool network_connected() { wifi_ap_record_t ap{}; return wifi_ok && esp_wifi_sta_get_ap_info(&ap)==ESP_OK; }
bool network_now_ready() { return now_ok; }
bool network_peer_recent() { return last_reply && uint32_t(esp_timer_get_time()/1000)-last_reply<30000; }
uint8_t network_channel() { uint8_t channel=0; wifi_second_chan_t second; if(wifi_ok) esp_wifi_get_channel(&channel,&second); return channel; }
void network_ip(char* buffer,size_t length) { esp_netif_ip_info_t ip{}; if(netif) esp_netif_get_ip_info(netif,&ip); snprintf(buffer,length,IPSTR,IP2STR(&ip.ip)); }
