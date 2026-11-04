#include "storage.h"
#include "face_media.h"
#include "sd_policy.h"
#include "maintenance.h"
#include "commissioning/sd_wire.h"
#include "driver/sdmmc_host.h"
#include "driver/gpio.h"
#include "sdmmc_cmd.h"
#include "esp_vfs_fat.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"
#include "nvs.h"
#include "ff.h"
#include "diskio_impl.h"
#include "diskio_sdmmc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>

namespace {
constexpr size_t Chunk=16384;
constexpr uint64_t FileBytes=1024ULL*1024*1024;
struct Snapshot {
    uint32_t schema=1,job=0,phase=0;
    char state[20]="PENDING",error[64]{},card_id[81]{},token[33]{};
    node::SdIdentity identity{};
    uint64_t fs_bytes=0,free_bytes=0,target=0,written=0,read=0,write_ms=0,read_ms=0,failed_offset=0;
    uint64_t expires=0;
    int probe_error=ESP_ERR_INVALID_STATE,mount_error=ESP_ERR_INVALID_STATE,fat_result=FR_NOT_READY;
    bool responding=false,mounted=false,fat32=false,io_ok=false,full=false;
};
struct Command { int op; node::SdIdentity expected; uint32_t job; };
Snapshot working,published;
node::SdPermit permit;
SemaphoreHandle_t guard;
QueueHandle_t commands;
std::atomic<bool> worker_ready{false};
std::atomic<int> display_state{0};
sdmmc_card_t card{};
FATFS* volume=nullptr;
BYTE drive=FF_DRV_NOT_USED;
char drive_name[3]{};
bool host_up=false;
uint64_t now_ms() {return esp_timer_get_time()/1000;}
const char* phase_name(unsigned phase) {
    static const char* names[]={"IDLE","INSPECTING","READY","FORMATTING","WRITING","READING","PASSED","FAILED","INTERRUPTED"};
    return phase<9?names[phase]:"UNKNOWN";
}
void publish() {
    xSemaphoreTake(guard,portMAX_DELAY); published=working; xSemaphoreGive(guard);
    display_state=!strcmp(working.state,"PASS")?1:working.phase>=3&&working.phase<=5?2:working.responding?3:4;
}
bool persist() {
    Snapshot saved=working; memset(saved.token,0,sizeof(saved.token)); saved.expires=0;
    nvs_handle_t nvs;
    if(nvs_open_from_partition("identity","sdtest",NVS_READWRITE,&nvs)!=ESP_OK) return false;
    bool ok=nvs_set_blob(nvs,"last",&saved,sizeof(saved))==ESP_OK && nvs_commit(nvs)==ESP_OK;
    nvs_close(nvs); return ok;
}
void fail(const char* message) {
    strlcpy(working.error,message,sizeof(working.error)); strlcpy(working.state,"FAIL",sizeof(working.state));
    working.phase=7; working.io_ok=false; working.expires=0; memset(working.token,0,sizeof(working.token)); publish();
}
void detach() {
    if(volume) { f_mount(nullptr,drive_name,0); esp_vfs_fat_unregister_path("/sd"); volume=nullptr; }
    if(drive!=FF_DRV_NOT_USED) {ff_diskio_unregister(drive);drive=FF_DRV_NOT_USED;}
    if(host_up) {sdmmc_host_deinit();host_up=false;}
}
void geometry() {
    FATFS* fs=nullptr; DWORD clusters=0;
    working.fat_result=f_getfree(drive_name,&clusters,&fs);
    if(working.fat_result==FR_OK) {
        working.fat32=fs->fs_type==FS_FAT32;
        working.fs_bytes=uint64_t(fs->n_fatent-2)*fs->csize*card.csd.sector_size;
        working.free_bytes=uint64_t(clusters)*fs->csize*card.csd.sector_size;
    }
}
// This function only reads card metadata and the existing filesystem.
bool probe() {
    detach(); card={}; working.responding=working.mounted=working.fat32=working.io_ok=false;
    working.identity={}; working.card_id[0]=0; working.fs_bytes=working.free_bytes=0;
    working.mount_error=ESP_ERR_INVALID_STATE;working.fat_result=FR_NOT_READY;
    sdmmc_host_t host=SDMMC_HOST_DEFAULT();host.max_freq_khz=SDMMC_FREQ_DEFAULT;
    sdmmc_slot_config_t slot=SDMMC_SLOT_CONFIG_DEFAULT();
    slot.width=1;slot.clk=GPIO_NUM_1;slot.cmd=GPIO_NUM_44;slot.d0=GPIO_NUM_17;slot.d1=slot.d2=slot.d3=GPIO_NUM_NC;
    gpio_pullup_en(GPIO_NUM_44);gpio_pullup_en(GPIO_NUM_17);
    working.probe_error=host.init();host_up=working.probe_error==ESP_OK;
    if(host_up)working.probe_error=sdmmc_host_init_slot(host.slot,&slot);
    if(working.probe_error==ESP_OK)working.probe_error=sdmmc_card_init(&host,&card);
    if(working.probe_error!=ESP_OK){strlcpy(working.state,"UNRESPONSIVE",sizeof(working.state));return false;}
    working.responding=true;
    working.identity={uint32_t(card.cid.mfg_id),uint32_t(card.cid.oem_id),uint32_t(card.cid.revision),uint32_t(card.cid.date),uint32_t(card.cid.serial),uint64_t(card.csd.capacity)*card.csd.sector_size,uint32_t(card.csd.sector_size),{}};
    memcpy(working.identity.name,card.cid.name,8);
    node::sd_identity_text(working.identity,working.card_id,sizeof(working.card_id));
    working.mount_error=ff_diskio_get_drive(&drive);
    if(working.mount_error==ESP_OK){
        ff_diskio_register_sdmmc(drive,&card);ff_sdmmc_set_disk_status_check(drive,true);
        drive_name[0]='0'+drive;drive_name[1]=':';drive_name[2]=0;
        esp_vfs_fat_conf_t cfg{};cfg.base_path="/sd";cfg.fat_drive=drive_name;cfg.max_files=3;
        working.mount_error=esp_vfs_fat_register_cfg(&cfg,&volume);
    }
    if(working.mount_error!=ESP_OK){strlcpy(working.state,"FAIL",sizeof(working.state));return true;}
    working.fat_result=f_mount(volume,drive_name,1);
    working.mount_error=working.fat_result==FR_OK?ESP_OK:ESP_FAIL;
    working.mounted=working.fat_result==FR_OK;
    if(working.mounted) geometry();
    strlcpy(working.state,working.fat32?"READY":working.mounted?"UNSUPPORTED":"UNMOUNTABLE",sizeof(working.state));
    return true;
}
bool same_probe(const node::SdIdentity& expected) {
    const auto identity=expected; // probe replaces working.identity.
    if(!probe()){fail("card_not_responding");return false;}
    if(!node::same_card(identity,working.identity)){fail("card_changed");return false;}
    return true;
}
bool format_card() {
    if(!volume||drive==FF_DRV_NOT_USED){fail("filesystem_driver_unavailable");return false;}
    f_mount(nullptr,drive_name,0);working.mounted=false;working.fat32=false;
    auto* buffer=heap_caps_malloc(4096,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL);
    if(!buffer){fail("format_buffer_unavailable");return false;}
    LBA_t partitions[4]={100,0,0,0};
    auto result=f_fdisk(drive,partitions,buffer);
    VolToPart[drive].pd=drive;VolToPart[drive].pt=1;
    const MKFS_PARM options={FM_FAT32,2,0,0,32768};
    if(result==FR_OK)result=f_mkfs(drive_name,&options,buffer,4096);
    working.fat_result=result;
    bool ok=result==FR_OK;
    if(ok){
        auto e=sdmmc_read_sectors(&card,buffer,0,1);
        const auto* b=static_cast<const uint8_t*>(buffer);
        auto little32=[](const uint8_t* p){return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24;};
        uint64_t start=little32(b+454),sectors=little32(b+458);
        ok=e==ESP_OK&&b[510]==0x55&&b[511]==0xaa&&(b[450]==0x0b||b[450]==0x0c)&&start>0&&sectors>0&&start+sectors<=card.csd.capacity;
        for(int i=1;i<4;++i)for(int j=0;j<16;++j)if(b[446+16*i+j])ok=false;
    }
    free(buffer);
    if(!ok){fail("format_or_mbr_verification_failed");return false;}
    return true;
}
void pattern(uint64_t* data,size_t bytes,uint64_t offset,uint64_t seed){
    for(size_t i=0;i<bytes/8;++i)data[i]=node::sd_pattern(offset/8+i,seed);
}
void path_for(char* out,size_t size,unsigned index){snprintf(out,size,"%s/FTEST/T%03u.DAT",drive_name,index);}
bool file_test(bool full) {
    // A fresh format ensures this directory belongs exclusively to this job.
    char directory[24];snprintf(directory,sizeof(directory),"%s/FTEST",drive_name);
    if(f_mkdir(directory)!=FR_OK){fail("test_directory_failed");return false;}
    geometry();
    unsigned files=full?unsigned((working.free_bytes+FileBytes-1)/FileBytes):1;
    if(!files||files>128){fail("invalid_file_count");return false;}
    char path[40];FIL file{};
    for(unsigned i=0;i<files;++i){
        path_for(path,sizeof(path),i);
        if(f_open(&file,path,FA_WRITE|FA_CREATE_NEW)!=FR_OK){fail("test_create_failed");return false;}
        if(f_close(&file)!=FR_OK){fail("test_close_failed");return false;}
    }
    geometry();
    working.target=full?working.free_bytes:std::min<uint64_t>(working.free_bytes,16ULL*1024*1024);
    if(!working.target||working.target%8){fail("invalid_test_extent");return false;}
    auto* buffer=static_cast<uint64_t*>(heap_caps_malloc(Chunk,MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL));
    if(!buffer){fail("test_buffer_unavailable");return false;}
    uint64_t seed=(uint64_t(esp_random())<<32)|esp_random();
    bool ok=true;
    for(int pass=0;pass<2&&ok;++pass){
        if(pass && (!same_probe(working.identity)||!working.fat32)){ok=false;break;}
        working.phase=pass?5:4;strlcpy(working.state,"TESTING",sizeof(working.state));publish();
        uint64_t begin=now_ms(),offset=0;
        for(unsigned i=0;i<files&&offset<working.target&&ok;++i){
            path_for(path,sizeof(path),i);
            FRESULT r=f_open(&file,path,pass?FA_READ:FA_WRITE);
            if(r!=FR_OK){working.fat_result=r;fail("test_open_failed");ok=false;break;}
            uint64_t amount=std::min(FileBytes,working.target-offset),done=0;
            if(pass && f_size(&file)!=amount){fail("test_file_size_changed");ok=false;}
            while(done<amount&&ok){
                UINT n=static_cast<UINT>(std::min(uint64_t(Chunk),amount-done)),actual=0;
                if(!pass){pattern(buffer,n,offset,seed);r=f_write(&file,buffer,n,&actual);}
                else r=f_read(&file,buffer,n,&actual);
                if(r!=FR_OK||actual!=n){working.fat_result=r;working.failed_offset=offset;fail(pass?"test_read_failed":"test_write_failed");ok=false;break;}
                if(pass)for(unsigned w=0;w<n/8;++w)if(buffer[w]!=node::sd_pattern(offset/8+w,seed)){
                    working.failed_offset=offset+8*w;fail("test_data_mismatch");ok=false;break;
                }
                if(!ok)break;
                done+=n;offset+=n;
                if(pass){working.read=offset;working.read_ms=now_ms()-begin;}else{working.written=offset;working.write_ms=now_ms()-begin;}
                if((offset%(1024*1024))==0)publish();
                vTaskDelay(1); // Radio, health, sensor and display tasks remain runnable.
            }
            if(!pass&&f_sync(&file)!=FR_OK){fail("test_sync_failed");ok=false;}
            if(f_close(&file)!=FR_OK){fail("test_close_failed");ok=false;}
        }
        if(pass)working.read_ms=now_ms()-begin;else working.write_ms=now_ms()-begin;
    }
    free(buffer);
    if(!ok)return false;
    for(unsigned i=0;i<files;++i){path_for(path,sizeof(path),i);if(f_unlink(path)!=FR_OK){fail("test_cleanup_failed");return false;}}
    if(f_unlink(directory)!=FR_OK){fail("test_cleanup_failed");return false;}
    geometry();return working.fat32&&working.fat_result==FR_OK;
}
void worker(void*) {
    Command command{};
    for(;;){
        if(xQueueReceive(commands,&command,portMAX_DELAY)!=pdTRUE)continue;
        if(command.op==4){face_media_load_sd();maintenance_release_storage();continue;}
        working.job=command.job;working.error[0]=0;working.token[0]=0;working.expires=0;
        working.target=working.written=working.read=working.write_ms=working.read_ms=working.failed_offset=0;
        working.full=command.op==3;working.phase=command.op==1?1:3;publish();
        if(command.op==1){
            if(probe() && node::sd_supported(working.identity)){
                uint8_t random[16];esp_fill_random(random,sizeof(random));
                for(unsigned i=0;i<16;++i)snprintf(working.token+2*i,3,"%02x",random[i]);
                working.phase=2;working.expires=now_ms()+120000;
                xSemaphoreTake(guard,portMAX_DELAY);permit.prepare(working.identity,working.token,now_ms());xSemaphoreGive(guard);
            }else fail(working.responding?"unsupported_geometry":"card_not_responding");
        }else{
            // Persist intent before the first write. A power loss can never turn
            // an interrupted qualification into a successful test on reboot.
            working.identity=command.expected;node::sd_identity_text(command.expected,working.card_id,sizeof(working.card_id));
            if(!persist())fail("cannot_record_destructive_intent");
            else if(same_probe(command.expected)){
                working.phase=3;publish();
                if(format_card() && same_probe(command.expected) && working.fat32 && file_test(working.full)){
                    working.io_ok=true;working.phase=6;strlcpy(working.state,"PASS",sizeof(working.state));
                }else if(working.phase!=7)fail("format_or_test_failed");
            }
            if(!persist())fail("cannot_record_result");
        }
        publish();maintenance_release_storage();
    }
}
}
void storage_init() {
    guard=xSemaphoreCreateMutex();commands=xQueueCreate(1,sizeof(Command));
    if(!guard||!commands)return;
    probe();
    // Retain the bounded, non-destructive bring-up read/write check.
    if(working.fat32){
        char path[32];snprintf(path,sizeof(path),"%s/%08lX.TMP",drive_name,(unsigned long)esp_random());
        FIL f{};uint8_t bytes[512],back[512];for(unsigned i=0;i<512;++i)bytes[i]=i^0xa5;UINT n=0;
        bool ok=f_open(&f,path,FA_WRITE|FA_CREATE_NEW)==FR_OK;
        if(ok){ok=f_write(&f,bytes,512,&n)==FR_OK&&n==512;if(f_sync(&f)!=FR_OK)ok=false;if(f_close(&f)!=FR_OK)ok=false;
            if(f_open(&f,path,FA_READ)==FR_OK){if(f_read(&f,back,512,&n)!=FR_OK||n!=512||memcmp(bytes,back,512))ok=false;if(f_close(&f)!=FR_OK)ok=false;}else ok=false;
            if(f_unlink(path)!=FR_OK)ok=false;
        }
        working.io_ok=ok;strlcpy(working.state,ok?"PASS":"FAIL",sizeof(working.state));
    }
    nvs_handle_t nvs;Snapshot saved{};size_t length=sizeof(saved);
    if(nvs_open_from_partition("identity","sdtest",NVS_READONLY,&nvs)==ESP_OK){
        bool valid=nvs_get_blob(nvs,"last",&saved,&length)==ESP_OK&&length==sizeof(saved)&&saved.schema==1;nvs_close(nvs);
        if(valid&&saved.job&&node::same_card(saved.identity,working.identity)){
            working.job=saved.job;working.phase=saved.phase;working.full=saved.full;working.target=saved.target;
            working.written=saved.written;working.read=saved.read;working.write_ms=saved.write_ms;working.read_ms=saved.read_ms;working.failed_offset=saved.failed_offset;
            strlcpy(working.error,saved.error,sizeof(working.error));
            if(saved.phase>=3&&saved.phase<=5){working.phase=8;strlcpy(working.error,"power_loss_or_restart",sizeof(working.error));}
        }
    }
    publish();worker_ready=xTaskCreate(worker,"sd_maintenance",8192,nullptr,1,nullptr)==pdPASS;
}
const char* storage_state(){switch(display_state.load()){case 1:return "PASS";case 2:return "TESTING";case 3:return "FAIL";case 4:return "UNRESPONSIVE";default:return "PENDING";}}
const char* storage_request(int op,const char* card_id,const char* token,uint32_t& job) {
    if(!worker_ready)return "storage_worker_unavailable";
    if(op<1||op>3)return "invalid_sd_operation";
    if(!maintenance_claim_storage())return "maintenance_busy";
    xSemaphoreTake(guard,portMAX_DELAY);
    bool ok=op==1;
    node::SdIdentity expected=permit.card;
    if(op!=1){
        char stamp[81];node::sd_identity_text(expected,stamp,sizeof(stamp));
        ok=card_id&&!strcmp(card_id,stamp)&&permit.consume(expected,token,now_ms());
        permit.valid=false;
    }else permit.valid=false;
    if(ok){job=esp_random();if(!job)job=1;Command c{op,expected,job};ok=xQueueSend(commands,&c,0)==pdTRUE;}
    xSemaphoreGive(guard);
    if(!ok){maintenance_release_storage();return "invalid_or_expired_card_permit";}
    return nullptr;
}
void storage_json(cJSON* root) {
    if(!guard)return;
    xSemaphoreTake(guard,portMAX_DELAY);Snapshot s=published;xSemaphoreGive(guard);
    auto* j=cJSON_AddObjectToObject(root,"sd");
    cJSON_AddStringToObject(j,"state",s.state);cJSON_AddStringToObject(j,"probe_error",esp_err_to_name(s.probe_error));
    cJSON_AddStringToObject(j,"mount_error",esp_err_to_name(s.mount_error));cJSON_AddNumberToObject(j,"fatfs_result",s.fat_result);
    cJSON_AddStringToObject(j,"presence",s.responding?"RESPONDING":"UNKNOWN");cJSON_AddBoolToObject(j,"autoformat",false);
    cJSON_AddStringToObject(j,"absence_note","No response does not distinguish absent card, connection fault or failed media");
    cJSON_AddBoolToObject(j,"maintenance_supported",worker_ready);cJSON_AddStringToObject(j,"destructive_scope","entire_node_sd_card_MBR_and_FAT32");
    if(s.responding){
        cJSON_AddStringToObject(j,"card_id",s.card_id);cJSON_AddNumberToObject(j,"capacity_bytes",s.identity.bytes);
        cJSON_AddNumberToObject(j,"filesystem_bytes",s.fs_bytes);cJSON_AddNumberToObject(j,"free_bytes",s.free_bytes);
        cJSON_AddNumberToObject(j,"sector_bytes",s.identity.sector);cJSON_AddNumberToObject(j,"card_serial",s.identity.serial);
        cJSON_AddNumberToObject(j,"manufacturer",s.identity.manufacturer);cJSON_AddNumberToObject(j,"oem_id",s.identity.oem);
        cJSON_AddNumberToObject(j,"revision",s.identity.revision);cJSON_AddNumberToObject(j,"manufacturing_date_raw",s.identity.date);
        char name[9]{};memcpy(name,s.identity.name,8);cJSON_AddStringToObject(j,"product_name",name);
        cJSON_AddStringToObject(j,"filesystem",s.fat32?"FAT32":s.mounted?"UNSUPPORTED":"UNMOUNTABLE");
        cJSON_AddStringToObject(j,"isolated_read_write",s.io_ok?"PASS":"PENDING");
    }
    auto* result=cJSON_AddObjectToObject(j,"test");
    cJSON_AddNumberToObject(result,"job",s.job);cJSON_AddStringToObject(result,"phase",phase_name(s.phase));
    cJSON_AddStringToObject(result,"mode",s.full?"full":"quick");cJSON_AddStringToObject(result,"error",s.error);
    cJSON_AddNumberToObject(result,"target_bytes",s.target);cJSON_AddNumberToObject(result,"written_bytes",s.written);cJSON_AddNumberToObject(result,"read_bytes",s.read);
    cJSON_AddNumberToObject(result,"write_ms",s.write_ms);cJSON_AddNumberToObject(result,"read_ms",s.read_ms);cJSON_AddNumberToObject(result,"failed_offset",s.failed_offset);
    cJSON_AddStringToObject(result,"capacity_verification",s.phase==6&&s.full?"USABLE_DATA_EXTENT_PASSED":"NOT_VERIFIED");
    cJSON_AddBoolToObject(result,"reboot_persistent",true);
    if(s.phase==2&&s.expires>now_ms()){
        cJSON_AddStringToObject(j,"format_token",s.token);cJSON_AddNumberToObject(j,"permit_remaining_ms",s.expires-now_ms());
    }
}
void storage_report(uint8_t* report,uint8_t code,uint32_t accepted_job) {
    using namespace flockwire;
    memset(report,0,flocksd::ReportSize);
    if(!guard){report[0]=uint8_t(Code::Storage);report[1]=1;return;}
    xSemaphoreTake(guard,portMAX_DELAY);Snapshot s=published;xSemaphoreGive(guard);
    report[0]=code;report[1]=1;report[2]=s.phase;
    report[3]=(s.responding?1:0)|(s.fat32?2:0)|(s.io_ok?4:0)|(s.full?8:0)|(worker_ready?16:0);
    put32(report+4,accepted_job?accepted_job:s.job);put32(report+8,s.probe_error);put32(report+12,s.fat_result);
    if(strlen(s.card_id)==80)for(unsigned i=0;i<40;++i){unsigned b=0;sscanf(s.card_id+2*i,"%2x",&b);report[16+i]=b;}
    if(s.phase==2&&s.expires>now_ms()){
        for(unsigned i=0;i<16;++i){unsigned b=0;sscanf(s.token+2*i,"%2x",&b);report[56+i]=b;}
        put32(report+136,s.expires-now_ms());
    }
    flocksd::put64(report+72,s.identity.bytes);flocksd::put64(report+80,s.fs_bytes);flocksd::put64(report+88,s.free_bytes);
    flocksd::put64(report+96,s.target);flocksd::put64(report+104,s.written);flocksd::put64(report+112,s.read);
    put32(report+120,s.write_ms);put32(report+124,s.read_ms);flocksd::put64(report+128,s.failed_offset);report[140]=flocksd::error_id(s.error);
}

void storage_seed_media(){
    if(!worker_ready || !maintenance_claim_storage())return;
    Command c{};c.op=4;if(xQueueSend(commands,&c,0)!=pdTRUE)maintenance_release_storage();
}
