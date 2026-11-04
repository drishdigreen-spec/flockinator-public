#include <cstdio>
#include <cstring>
#include <cstdlib>
#include "node_model.h"
#include "sensors.h"
#include "display.h"
#include "mission.h"
#include "audio.h"
#include "storage.h"
#include "network.h"
#include "maintenance.h"
#include "node_link.h"
#include "ripples.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_app_desc.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_heap_caps.h"
#include "esp_mac.h"
#include "esp_ota_ops.h"
#include "esp_psram.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "cJSON.h"

static char mac[18]{}, label[3]="--";
static nvs_handle_t identity;
static bool nvs_ok=false, ram_ok=false;
static uint32_t boots=0;
static const char* str(cJSON* j,const char* k) { auto* v=cJSON_GetObjectItemCaseSensitive(j,k); return cJSON_IsString(v)?v->valuestring:""; }
static void emit(cJSON* j) { char* s=cJSON_PrintUnformatted(j); if(s) { puts(s); fflush(stdout); free(s); } cJSON_Delete(j); }
static cJSON* status() {
    auto* j=cJSON_CreateObject();
    cJSON_AddNumberToObject(j,"v",1); cJSON_AddStringToObject(j,"type","status");
    cJSON_AddStringToObject(j,"base_mac",mac); cJSON_AddStringToObject(j,"label",label);
    cJSON_AddStringToObject(j,"firmware",esp_app_get_description()->version);
    auto* running=esp_ota_get_running_partition();
    cJSON_AddStringToObject(j,"running_partition",running->label);
    esp_ota_img_states_t ota_state=ESP_OTA_IMG_UNDEFINED;
    esp_ota_get_state_partition(running,&ota_state); cJSON_AddNumberToObject(j,"ota_state",ota_state);
    char sha[65]; for(int i=0;i<32;i++) snprintf(sha+i*2,3,"%02x",esp_app_get_description()->app_elf_sha256[i]); cJSON_AddStringToObject(j,"elf_sha256",sha);
    uint8_t digest[32]; esp_partition_get_sha256(esp_ota_get_running_partition(),digest);
    for(int i=0;i<32;i++) snprintf(sha+i*2,3,"%02x",digest[i]); cJSON_AddStringToObject(j,"app_sha256",sha);
    uint32_t flash=0; esp_flash_get_size(nullptr,&flash); cJSON_AddNumberToObject(j,"flash_bytes",flash);
    cJSON_AddNumberToObject(j,"psram_bytes",esp_psram_get_size());
    cJSON_AddStringToObject(j,"psram_sample",ram_ok?"PASS":"FAIL");
    cJSON_AddNumberToObject(j,"psram_sample_bytes",65536);
    cJSON_AddStringToObject(j,"identity_nvs",nvs_ok?"PASS":"FAIL");
    cJSON_AddNumberToObject(j,"boot_count",boots); cJSON_AddNumberToObject(j,"reset_reason",esp_reset_reason());
    cJSON_AddNumberToObject(j,"uptime_ms",esp_timer_get_time()/1000);
    cJSON_AddNumberToObject(j,"free_internal",heap_caps_get_free_size(MALLOC_CAP_INTERNAL));
    cJSON_AddNumberToObject(j,"min_internal",heap_caps_get_minimum_free_size(MALLOC_CAP_INTERNAL));
    cJSON_AddNumberToObject(j,"free_dma",heap_caps_get_free_size(MALLOC_CAP_DMA));
    cJSON_AddNumberToObject(j,"largest_internal_block",heap_caps_get_largest_free_block(MALLOC_CAP_INTERNAL));
    ripples_json(j); sensors_json(j); display_json(j); audio_json(j); storage_json(j); network_json(j); maintenance_json(j); node_link_json(j); return j;
}
static void command(const char* line) {
    auto* req=cJSON_Parse(line); auto* out=status(); const char* op=str(req,"op");
    bool valid=req && cJSON_IsNumber(cJSON_GetObjectItem(req,"v")) && cJSON_GetObjectItem(req,"v")->valuedouble==1;
    const char* error=valid?nullptr:"invalid_request";
    if(!error && strcmp(op,"status")) {
        if(strcmp(str(req,"target"),mac)) error="wrong_target";
        else if(!strcmp(op,"provision")) {
            const char* wanted=str(req,"label");
            if(!node::valid_label(wanted)) error="invalid_label";
            else if(!nvs_ok) error="nvs_unavailable";
            else if(strcmp(label,"--") && strcmp(label,wanted)) error="identity_already_assigned";
            else if(nvs_set_str(identity,"label",wanted)!=ESP_OK || nvs_commit(identity)!=ESP_OK) error="nvs_write_failed";
            else { size_t n=sizeof(label); if(nvs_get_str(identity,"label",label,&n)!=ESP_OK || strcmp(label,wanted)) error="nvs_readback_failed"; }
        } else if(!strcmp(op,"set_key")) { if(!maintenance_set_key(str(req,"key"))) error="key_provision_failed"; } else if(!strcmp(op,"wifi")) { if(!network_configure(str(req,"ssid"),str(req,"password"))) error="wifi_configuration_failed"; } else if(!strcmp(op,"tone")) { if(!audio_tone()) error="tone_failed"; } else if(!strcmp(op,"next_page")) { display_next_page(); } else if(!strncmp(op,"mission_",8)) { error=mission_command(req); } else if(!strncmp(op,"display_",8)) { error=display_command(req); } else if(!strncmp(op,"sd_",3)) {
            int action=!strcmp(op,"sd_prepare")?1:!strcmp(op,"sd_format_quick")?2:!strcmp(op,"sd_format_full")?3:0;
            uint32_t job=0;error=storage_request(action,str(req,"card_id"),str(req,"token"),job);
            if(!error)cJSON_AddNumberToObject(out,"sd_job",job);
        } else if(!strcmp(op,"reboot")) { if(maintenance_storage_busy())error="maintenance_busy"; }
        else error="unsupported_operation";
        if(!error && strncmp(op,"sd_",3)) { cJSON_Delete(out); out=status(); }
    }
    cJSON_AddStringToObject(out,"request_id",str(req,"id"));
    cJSON_AddBoolToObject(out,"ok",!error); if(error) cJSON_AddStringToObject(out,"error",error);
    bool reboot=!error && !strcmp(op,"reboot"); emit(out); cJSON_Delete(req);
    if(reboot) { vTaskDelay(pdMS_TO_TICKS(200)); esp_restart(); }
}
extern "C" void app_main() {
    setvbuf(stdin,nullptr,_IONBF,0); setvbuf(stdout,nullptr,_IONBF,0);
    uint8_t id[6]; ESP_ERROR_CHECK(esp_efuse_mac_get_default(id));
    snprintf(mac,sizeof(mac),"%02X:%02X:%02X:%02X:%02X:%02X",id[0],id[1],id[2],id[3],id[4],id[5]);
    nvs_ok=nvs_flash_init_partition("identity")==ESP_OK && nvs_open_from_partition("identity","node",NVS_READWRITE,&identity)==ESP_OK;
    if(nvs_ok) {
        size_t len=sizeof(label); nvs_get_str(identity,"label",label,&len); if(!node::valid_label(label)) strcpy(label,"--");
        nvs_get_u32(identity,"boots",&boots); ++boots;
        nvs_ok=nvs_set_u32(identity,"boots",boots)==ESP_OK && nvs_commit(identity)==ESP_OK;
    }
    auto* ram=static_cast<uint32_t*>(heap_caps_malloc(65536,MALLOC_CAP_SPIRAM));
    ram_ok=ram; if(ram) { for(uint32_t pass=0;pass<2;pass++) { for(uint32_t i=0;i<16384;i++) ram[i]=(i*2654435761u)^(pass?0xAAAAAAAA:0x55555555); for(uint32_t i=0;i<16384;i++) if(ram[i]!=((i*2654435761u)^(pass?0xAAAAAAAA:0x55555555))) ram_ok=false; } free(ram); }
    // Only core service health validates a boot; missing peripherals do not roll back.
    #ifdef FLOCK_TEST_REJECT_BOOT
    esp_restart(); // Explicit recovery-test image only; never used for a normal build.
#endif
    mission_init(label); sensors_init(); sensors_poll(); display_init(); audio_init(); storage_init(); network_init(); maintenance_init(mac); node_link_init();storage_seed_media();
    if(nvs_ok && ram_ok && maintenance_ready() && node_link_ready()) esp_ota_mark_app_valid_cancel_rollback();
    auto* initial=status(); maintenance_publish(initial); emit(initial); node::LineBuffer buffer; uint32_t last=0,last_audio=0;
    while(true) { if(!maintenance_busy()) { ripples_tick(label); display_tick(label,ram_ok); network_tick(label); maintenance_tick(); } uint32_t now=esp_timer_get_time()/1000; if(now-last>=2000 && !maintenance_busy()) { sensors_poll(); last=now; auto* snapshot=status(); maintenance_publish(snapshot); cJSON_Delete(snapshot); } if(now-last_audio>=250 && !maintenance_busy()) { audio_poll(); last_audio=now; } int ch=getchar(); if(ch==EOF) { clearerr(stdin); vTaskDelay(pdMS_TO_TICKS(10)); continue; } auto r=buffer.push(static_cast<char>(ch)); if(r==node::LineBuffer::Ready) command(buffer.data()); else if(r==node::LineBuffer::Overflow) puts("{\"v\":1,\"ok\":false,\"error\":\"request_too_large\"}"); }
}
