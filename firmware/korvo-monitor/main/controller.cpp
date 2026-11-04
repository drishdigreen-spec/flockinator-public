#include "controller.h"
#include "fleet.h"
#include "board_model.h"
#include "esp_http_server.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "esp_rom_crc.h"
#include "nvs.h"
#include <dirent.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <algorithm>
#include <unistd.h>

namespace {
constexpr const char* root="/sdcard/flockinator/runs";
nvs_handle_t ns;
SemaphoreHandle_t board_lock;
Json plan;
string cached;
uint32_t cache_rev;
int cache_turn=-1;
unsigned pin;
int64_t reject_until;
int64_t millis(){return esp_timer_get_time()/1000;}
int64_t utc_ms(){timeval tv{};gettimeofday(&tv,nullptr);return int64_t(tv.tv_sec)*1000+tv.tv_usec/1000;}
bool synced(){return utc_ms()>1700000000000LL;}
bool exists(const string& p){struct stat s;return stat(p.c_str(),&s)==0;}
bool valid_id(const string& id){return id.size()==30 && id[13]=='-' && id.substr(0,13).find_first_not_of("0123456789")==string::npos && id.substr(14).find_first_not_of("0123456789abcdef")==string::npos;}
string dir(const string& id){return string(root)+"/"+id;}
bool write_file(const string& p,const string& data){
    auto f=fopen(p.c_str(),"wb");if(!f)return false;bool ok=fwrite(data.data(),1,data.size(),f)==data.size();
    if(fclose(f)!=0)ok=false;
    return ok;
}
bool read_file(const string& p,string& data,size_t limit=1024*1024){
    auto f=fopen(p.c_str(),"rb");if(!f)return false;
    fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);
    if(n<0||size_t(n)>limit){fclose(f);return false;}
    data.resize(n);bool ok=fread(data.data(),1,n,f)==size_t(n);fclose(f);return ok;
}
std::vector<string> run_ids(){
    std::vector<string> ids;auto d=opendir(root);if(!d)return ids;
    while(auto e=readdir(d))if(valid_id(e->d_name))ids.emplace_back(e->d_name);
    closedir(d);std::sort(ids.rbegin(),ids.rend());return ids;
}
int turns(const Json& p){
    int t=p["turn"];if(p["phase"]=="Running"&&synced()&&p["since"].is_number())
        t+=std::clamp<int64_t>((utc_ms()-p["since"].get<int64_t>())/1000,0,46);
    return std::min(t,46);
}
string stamp(int64_t ms){time_t sec=ms/1000;tm t{};gmtime_r(&sec,&t);char date[32],out[45];strftime(date,sizeof(date),"%Y-%m-%dT%H:%M:%S",&t);snprintf(out,sizeof(out),"%s.%03dZ",date,int(ms%1000));return out;}
struct File {string name,data;};
std::vector<File> records(const Json& p,string phase){
    Json journals=Json::array();for(int i=0;i<p["count"].get<int>();i++)journals.push_back(Json::array());
    Json v=board::simulate(p,turns(p),&journals);
    auto seg=p["segments"];Json manifest={{"schema",1},{"source","planner_simulation"},{"ruleset","search-board-1"},{"run",p["episode"]},
        {"phase",phase.empty()?v["phase"]:Json(phase)},{"last_turn",v["sim"]["turn"]},{"started_utc",stamp(seg[0][1])},{"ground_truth",p["contacts"]},{"scenario",p},{"units",Json::array()},{"clock_segments",Json::array()}};
    for(auto& s:seg)manifest["clock_segments"].push_back({s[0],s[1].get<int64_t>()/1000.0});
    manifest["scenario"].erase("contacts");manifest["scenario"].erase("segments");manifest["scenario"].erase("since");
    std::vector<File> files;
    for(size_t i=0;i<journals.size();i++){
        string lines;unsigned seq=0;manifest["units"].push_back(unit_label(i));
        for(auto& e:journals[i]){
            int tick=e["turn"],base=0;int64_t epoch=seg[0][1];
            for(auto& s:seg)if(s[0]<tick){base=s[0];epoch=s[1];}
            e["seq"]=++seq;e["utc"]=stamp(epoch+(tick-base)*1000);e["schema"]=1;e["run"]=p["episode"];e["source"]="planner_simulation";e["ruleset"]="search-board-1";
            lines+=e.dump();lines+='\n';
        }
        files.push_back({unit_label(i)+".jsonl",std::move(lines)});
    }
    files.push_back({"director.json",manifest.dump()});return files;
}
// Standard ZIP32 stored entries. No decompressor or remote archive service is needed.
void le16(string& s,uint32_t v){s.push_back(char(v));s.push_back(char(v>>8));}
void le32(string& s,uint32_t v){le16(s,v);le16(s,v>>16);}
string zip(const std::vector<File>& files){
    string out,central;
    for(auto& f:files){
        uint32_t offset=out.size(),size=f.data.size(),crc=esp_rom_crc32_le(0,(const uint8_t*)f.data.data(),size);
        string h;le16(h,20);le16(h,0);le16(h,0);le16(h,0);le16(h,33);le32(h,crc);le32(h,size);le32(h,size);le16(h,f.name.size());le16(h,0);
        le32(out,0x04034b50);out+=h;out+=f.name;out+=f.data;
        le32(central,0x02014b50);le16(central,20);central+=h;le16(central,0);le16(central,0);le16(central,0);le32(central,0);le32(central,offset);central+=f.name;
    }
    uint32_t offset=out.size();out+=central;le32(out,0x06054b50);le16(out,0);le16(out,0);le16(out,files.size());le16(out,files.size());le32(out,central.size());le32(out,offset);le16(out,0);return out;
}
bool finalize(const Json& p,const string& phase){
    if(!p.contains("episode"))return true;
    string d=dir(p["episode"]);if(exists(d+"/closed"))return true;
    if(mkdir(root,0755)&&errno!=EEXIST)return false;
    if(mkdir(d.c_str(),0755)&&errno!=EEXIST)return false;
    auto files=records(p,phase);
    for(auto& f:files)if(!write_file(d+"/"+f.name,f.data))return false;
    if(!write_file(d+"/archive.zip",zip(files)))return false;
    return write_file(d+"/closed","1");
}
Json history(){
    Json arr=Json::array();
    for(auto& id:run_ids()){
        string d=dir(id);if(!exists(d+"/closed"))continue;
        Json verified=Json::array();for(int i=0;i<16;i++)if(exists(d+"/"+unit_label(i)+".ok"))verified.push_back(unit_label(i));
        arr.push_back({{"run",id},{"verified",verified},{"finalized",true}});
    }
    if(plan.contains("episode")&&!exists(dir(plan["episode"])+"/closed"))
        arr.insert(arr.begin(),Json{{"run",plan["episode"]},{"verified",Json::array()},{"finalized",false}});
    return arr;
}
bool save(const Json& next){
    string blob=next.dump();if(nvs_set_blob(ns,"board",blob.data(),blob.size())!=ESP_OK||nvs_commit(ns)!=ESP_OK)return false;
    plan=next;cache_turn=-1;return true;
}
string view(){
    int t=turns(plan);uint32_t rev=plan["revision"];
    if(cache_turn!=t||cache_rev!=rev){auto v=board::simulate(plan,t);cached=v.dump();cache_turn=t;cache_rev=rev;}
    return cached;
}
bool mutate(const Json& a,string& error){
    if(!a.contains("revision")||a["revision"]!=plan["revision"]){error="Plan changed. Refresh before retrying.";return false;}
    if(!a.contains("op")||!a["op"].is_string()){error="Invalid action";return false;}
    string op=a["op"];Json next=plan;
    auto v=board::simulate(plan,turns(plan));string phase=v["phase"];int t=v["sim"]["turn"];
    if(op=="play"&&(phase=="Draft"||phase=="Paused")){
        if(!synced()){error="Open the controller dashboard to set its clock";return false;}
        if(!exists("/sdcard/flockinator")){error="Controller SD card unavailable";return false;}
        auto now=utc_ms();if(phase=="Draft"){char id[48];snprintf(id,sizeof(id),"%013lld-%08lx%08lx",(long long)now,(unsigned long)esp_random(),(unsigned long)esp_random());next["episode"]=id;next["segments"]=Json::array();}
        if(next["segments"].size()>=128){error="Pause history full. Close the rehearsal.";return false;}
        next["segments"].push_back({t,now});next["phase"]="Running";next["since"]=now;
    }else if(op=="pause"&&phase=="Running"){next["phase"]="Paused";next["turn"]=t;next["since"]=nullptr;}
    else if(op=="assess"&&a.contains("index")&&natural(a["index"],23)&&a["index"].get<size_t>()<next["contacts"].size()&&a.contains("outcome")&&
        (a["outcome"]=="Intact"||a["outcome"]=="Damaged"||a["outcome"]=="Removed"||a["outcome"]=="Unassessed")){
        next["contacts"][a["index"].get<int>()]["outcome"]=a["outcome"];
    }else if(op=="edit"||((phase=="Complete"||phase=="Draft")&&op=="randomize")){
        if(op=="randomize"&&a.contains("seed")&&!a["seed"].is_null()&&!natural(a["seed"],UINT32_MAX)){error="Invalid seed";return false;}
        if(!finalize(plan,phase=="Complete"?phase:"Ended early")){error="Cannot close SD journal";return false;}
        if(op=="randomize")next=board::generate(a.contains("seed")&&!a["seed"].is_null()?a["seed"].get<uint32_t>():esp_random());
        else{next.erase("episode");next.erase("segments");next["since"]=nullptr;next["turn"]=0;next["phase"]="Draft";}
    }else if(phase!="Draft"||!board::edit(next,a,error)){if(error.empty())error="Return to planning first";return false;}
    next["revision"]=plan["revision"].get<uint32_t>()+1u;
    if(!save(next)){error="Cannot persist planner";return false;}return true;
}
esp_err_t reply(httpd_req_t* r,const string& s,const char* mime="application/json"){
    httpd_resp_set_type(r,mime);httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_send(r,s.data(),s.size());
}
bool authorized(httpd_req_t* r){
    char host[32],origin[64],value[16];esp_netif_ip_info_t info{};
    auto net=esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");if(!net||esp_netif_get_ip_info(net,&info)!=ESP_OK)return false;
    char ip[20];snprintf(ip,sizeof(ip),IPSTR,IP2STR(&info.ip));
    if(httpd_req_get_hdr_value_str(r,"Host",host,sizeof(host))!=ESP_OK||strcmp(ip,host))return false;
    if(httpd_req_get_hdr_value_len(r,"Origin")&&(httpd_req_get_hdr_value_str(r,"Origin",origin,sizeof(origin))!=ESP_OK||"http://"+string(host)!=origin))return false;
    if(httpd_req_get_hdr_value_str(r,"X-Flock-Operator",value,sizeof(value))!=ESP_OK||!value[0])return false;
    if(millis()<reject_until)return false;
    if(std::to_string(pin)!=value){reject_until=millis()+1500;return false;}return true;
}
string receive_body(httpd_req_t* r,size_t max){
    if(!r->content_len||r->content_len>max)return {};
    string body(r->content_len,'\0');for(size_t n=0;n<body.size();){int k=httpd_req_recv(r,body.data()+n,body.size()-n);if(k<=0)return {};n+=k;}return body;
}
void set_clock(httpd_req_t* r){
    if(synced())return;
    char value[24];if(httpd_req_get_hdr_value_str(r,"X-Flock-Time",value,sizeof(value))!=ESP_OK)return;
    char* end;long long t=strtoll(value,&end,10);if(*end||t<1700000000000LL||t>4102444800000LL)return;
    timeval tv={.tv_sec=time_t(t/1000),.tv_usec=(suseconds_t)(t%1000*1000)};settimeofday(&tv,nullptr);
}
extern "C" const char home_html[] asm("_binary_index_html_start"),app_js[] asm("_binary_app_js_start"),style_css[] asm("_binary_style_css_start"),
    plan_html[] asm("_binary_planner_html_start"),plan_js[] asm("_binary_planner_js_start"),plan_css[] asm("_binary_planner_css_start"),operator_js[] asm("_binary_operator_js_start");
esp_err_t handler(httpd_req_t* r){
    string path=r->uri;
    if(r->method==HTTP_POST){
        if(!authorized(r)){httpd_resp_set_status(r,"401 Unauthorized");return reply(r,"{\"error\":\"Enter the operator PIN shown on the Korvo\"}");}
        set_clock(r);
        const string prefix="/api/import/";
        if(path.compare(0,prefix.size(),prefix)==0){
            string id=path.substr(prefix.size()),d=dir(id);char mask[8]{};
            if(!valid_id(id)||httpd_req_get_hdr_value_str(r,"X-Verified-Mask",mask,sizeof(mask))!=ESP_OK||strlen(mask)!=4||strspn(mask,"0123456789abcdef")!=4)return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid archive metadata");
            string bytes=receive_body(r,512*1024);if(bytes.size()<22||memcmp(bytes.data(),"PK\x03\x04",4))return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Invalid archive");
            Guard l(board_lock);if(exists(d+"/closed"))return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Already archived");
            mkdir(root,0755);mkdir(d.c_str(),0755);
            if(!write_file(d+"/archive.zip",bytes))return httpd_resp_send_err(r,HTTPD_500_INTERNAL_SERVER_ERROR,"SD write failed");
            unsigned bits=strtoul(mask,nullptr,16);for(int i=0;i<16;i++)if(bits&(1<<i))if(!write_file(d+"/"+unit_label(i)+".ok","Imported prior readback receipt"))return ESP_FAIL;
            if(!write_file(d+"/closed","imported"))return ESP_FAIL;
            return reply(r,"{\"ok\":true}");
        }
        auto a=Json::parse(receive_body(r,2048),nullptr,false);if(!a.is_object())return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Expected JSON object");
        string error;
        if(path=="/api/mission"){if(fleet_command(a,error))return reply(r,"{\"ok\":true}");}
        else{Guard l(board_lock);if(mutate(a,error))return reply(r,view());}
        httpd_resp_set_status(r,"409 Conflict");return reply(r,Json{{"error",error}}.dump());
    }
    if(path=="/api/fleet")return reply(r,fleet_snapshot().dump());
    if(path=="/api/planner"){string s;{Guard l(board_lock);s=view();}return reply(r,s);}
    if(path=="/api/planner/journals"){Guard l(board_lock);return reply(r,history().dump());}
    const string prefix="/api/planner/journals/";
    if(path.compare(0,prefix.size(),prefix)==0){
        auto id=path.substr(prefix.size());if(id.size()!=34||id.substr(30)!=".zip"||!valid_id(id.substr(0,30)))return httpd_resp_send_err(r,HTTPD_404_NOT_FOUND,"Unknown journal");
        id.resize(30);string data;
        {Guard l(board_lock);if(!read_file(dir(id)+"/archive.zip",data)){
            if(!plan.contains("episode")||plan["episode"]!=id)return httpd_resp_send_err(r,HTTPD_404_NOT_FOUND,"Unknown journal");
            data=zip(records(plan,""));}}
        return reply(r,data,"application/zip");
    }
    const char* text=path=="/"?home_html:path=="/app.js"?app_js:path=="/style.css"?style_css:path=="/planner"?plan_html:path=="/planner.js"?plan_js:path=="/planner.css"?plan_css:operator_js;
    httpd_resp_set_type(r,path.size()>3&&path.substr(path.size()-3)==".js"?"text/javascript":path.size()>4&&path.substr(path.size()-4)==".css"?"text/css":"text/html");
    httpd_resp_set_hdr(r,"Content-Security-Policy","default-src 'self'; frame-ancestors 'none'");httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_sendstr(r,text);
}
}
void archive_tick(){
    Guard l(board_lock);
    if(!plan.contains("episode")||exists(dir(plan["episode"])+"/closed")||!synced())return;
    auto v=board::simulate(plan,turns(plan));if(v["phase"]=="Complete")finalize(plan,"Complete");
}
void deliver_next(int i){
    string label=string(1,char('A'+i/4))+char('1'+i%4);
    for(const auto& id:run_ids()){
        string d=dir(id);if(!exists(d+"/closed")||exists(d+"/"+label+".ok")||!exists(d+"/"+label+".jsonl"))continue;
        string bytes,reply;if(!read_file(d+"/"+label+".jsonl",bytes,131072))return;
        string digest=sha256hex(bytes);if(!signed_panel(i,"POST","/v1/journal",bytes,reply))return;
        auto a=Json::parse(reply,nullptr,false);if(!a.is_object()||a.value("ok",false)!=true||a.value("sha256",string{})!=digest||a.value("bytes",0u)!=bytes.size())return;
        if(signed_panel(i,"POST","/v1/journal/read",digest,reply)&&reply==bytes)write_file(d+"/"+label+".ok",digest);
        return;
    }
}
extern "C" unsigned standalone_pin(){return pin;}
extern "C" bool standalone_usb(const char* line){return fleet_provision(line);}
extern "C" void standalone_init(){
    if(nvs_open("standalone",NVS_READWRITE,&ns)!=ESP_OK)return;
    board_lock=xSemaphoreCreateMutex();pin=100000+esp_random()%900000;
    plan=board::initial();size_t n=0;
    if(nvs_get_blob(ns,"board",nullptr,&n)==ESP_OK&&n<=16000){
        string tmp(n,'\0');if(nvs_get_blob(ns,"board",tmp.data(),&n)==ESP_OK){auto saved=Json::parse(tmp,nullptr,false);if(saved.is_object()&&saved.contains("revision"))plan=saved;}
    }
    mkdir(root,0755);fleet_init(ns);
    xTaskCreate([](void*){for(;;){vTaskDelay(pdMS_TO_TICKS(1200));archive_tick();}},"journal_close",24576,nullptr,1,nullptr);
}
extern "C" void standalone_web(void* handle){
    auto server=static_cast<httpd_handle_t>(handle);
    for(const char* path:{"/","/app.js","/style.css","/operator.js","/planner","/planner.js","/planner.css","/api/fleet","/api/planner","/api/planner/journals","/api/planner/journals/*"}){
        httpd_uri_t ep{};ep.uri=path;ep.method=HTTP_GET;ep.handler=handler;ESP_ERROR_CHECK(httpd_register_uri_handler(server,&ep));
    }
    for(const char* path:{"/api/mission","/api/planner","/api/import/*"}){
        httpd_uri_t ep{};ep.uri=path;ep.method=HTTP_POST;ep.handler=handler;ESP_ERROR_CHECK(httpd_register_uri_handler(server,&ep));
    }
}
