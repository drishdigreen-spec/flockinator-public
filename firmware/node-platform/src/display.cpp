#ifdef FLOCK_PATTERNFLOW_TRIAL
#include "patternflow/adapter.h"
#endif
#include "display.h"
#include "ripples.h"
#include "mission.h"
#include "recon_render.h"
#include "world_render.h"
#include "mission_world.h"
#include "survey_command.h"
#include "avatar_render.h"
#include "random_expression.h"
#include "face_media.h"
#include "maintenance.h"
#include "esp_mac.h"
#include "pixel_ui.h"
#include "node_model.h"
#include "sensors.h"
#include "audio.h"
#include "storage.h"
#include "network.h"
#include "hub75.h"
#include "driver/gpio.h"
#include "esp_timer.h"
#include <cstdio>
static Hub75Driver* panel;
static bool panel_ok=false;
static node::Frame frame,recon_scratch;
static bool mission_view=true;
static bool world_view=true;
static world::Runtime world_runtime;
static survey::Runtime survey_runtime;
static world::Sensor world_sensor=world::Cam;
static world::Sample world_sample{};
static int world_index=0;
static uint32_t world_timings[256]{},world_count=0,world_max_us=0;

static uint32_t displayed_run=0;
static uint32_t last_frame=0,last_page=0,last_press=0,presses=0;
static int page=0,previous_button=1;
static bool long_press_fired=false;
static bool avatar_view=true,injury_profile=false,observed_warning=false;
static node::AvatarState avatar;
static node::RandomExpression random_expression;
static uint32_t avatar_seed=1,rendered=0,dropped=0,last_duration_us=0;
static const char* world_command(cJSON* req,uint32_t now){
    const char* action="start";auto sensor=world_sensor;
    for(auto* v=req->child;v;v=v->next){
        if(!v->string)return "invalid_field";
        for(auto* prior=req->child;prior!=v;prior=prior->next)if(!strcmp(prior->string,v->string))return "duplicate_field";
        if(!strcmp(v->string,"action")){if(!cJSON_IsString(v))return "invalid_world_action";action=v->valuestring;}
        else if(!strcmp(v->string,"sensor")){if(!cJSON_IsString(v))return "invalid_world_sensor";int found=-1;for(int i=0;i<5;i++)if(!strcmp(v->valuestring,world::sensor_name(world::Sensor(i))))found=i;if(found<0)return "invalid_world_sensor";sensor=world::Sensor(found);}
        else if(strcmp(v->string,"op")&&strcmp(v->string,"v")&&strcmp(v->string,"id")&&strcmp(v->string,"target"))return "unknown_world_field";
    }
    bool start=!strcmp(action,"start");
    if(!start&&!world_view)return "world_not_active";
    if(start){survey_runtime.active=false;world_runtime.start(now);world_count=0;world_max_us=0;}
    else if(!strcmp(action,"pause"))world_runtime.pause(now);
    else if(!strcmp(action,"play"))world_runtime.play(now);
    else if(!strcmp(action,"interrupt"))world_runtime.interrupt(now);
    else if(!strcmp(action,"resume"))world_runtime.resume(now,world_index);
    else if(!strcmp(action,"impact")){if(!world_runtime.impact(now,world_index))return "impact_unavailable";}
    else if(strcmp(action,"sensor"))return "invalid_world_action";
    auto mission=mission_snapshot();if(mission.config.run)mission_apply(mission.config,false,0);
    world_sensor=sensor;world_view=true;avatar_view=true;last_frame=0;return nullptr;
}
static node::AvatarState effective(uint32_t now){
    auto state=avatar;
    if(state.demo && !random_expression.enabled && state.active(now)){
        unsigned step=((now-state.started)/3000)%7;
        state.activity=step==0?node::Activity::Sleeping:step==2?node::Activity::Listening:step==3?node::Activity::Processing:step==5?node::Activity::Speaking:node::Activity::Idle;
        state.mood=step==1?node::Mood::Curious:step==4?node::Mood::Content:step==6?node::Mood::Frightened:node::Mood::Neutral;
        state.attention=step==6?node::Attention::Urgent:node::Attention::Calm;
    }
    return state;
}
const char* display_command(cJSON* req){
    auto* operation=cJSON_GetObjectItemCaseSensitive(req,"op");
    if(cJSON_IsString(operation)&&!strncmp(operation->valuestring,"mission_",8))return mission_command(req);
    auto text=[&](const char* k){auto* v=cJSON_GetObjectItemCaseSensitive(req,k);return cJSON_IsString(v)?v->valuestring:"";};
    const char* op=text("op");uint32_t now=esp_timer_get_time()/1000;
    if(!strcmp(op,"display_survey")){
        survey::Packet packet{};
        if(!survey::parse(req,packet)||!survey_runtime.receive(packet,world_index,now))return "invalid_survey_snapshot";
        if(!world_view){world_count=0;world_max_us=0;}
        world_view=true;mission_view=false;avatar_view=true;return nullptr;
    }
    if(!strcmp(op,"display_world"))return world_command(req,now);
    const bool state=!strcmp(op,"display_state"),profile=!strcmp(op,"display_profile");
    if(!state&&!profile&&strcmp(op,"display_auto")&&strcmp(op,"display_demo")&&strcmp(op,"display_random"))return "unsupported_display_operation";
    for(auto* v=req->child;v;v=v->next){
        const char* k=v->string;
        if(!k)return "invalid_field";
        for(auto* prior=req->child;prior!=v;prior=prior->next)if(prior->string&&!strcmp(prior->string,k))return "duplicate_field";
        bool allowed=!strcmp(k,"op")||!strcmp(k,"v")||!strcmp(k,"target")||!strcmp(k,"id")||(profile&&!strcmp(k,"profile"))||(state&&(!strcmp(k,"activity")||!strcmp(k,"attention")||!strcmp(k,"mood")||!strcmp(k,"vitality")||!strcmp(k,"ttl")));
        if(!allowed)return "unknown_display_field";
    }
    if(state){
        int a=-1,t=0,m=0,v=-1;for(int i=0;i<6;i++)if(!strcmp(text("activity"),node::activity_name(node::Activity(i))))a=i;
        if(cJSON_HasObjectItem(req,"attention")){t=-1;for(int i=0;i<3;i++)if(!strcmp(text("attention"),node::attention_name(node::Attention(i))))t=i;}
        if(cJSON_HasObjectItem(req,"mood")){m=-1;for(int i=0;i<4;i++)if(!strcmp(text("mood"),node::mood_name(node::Mood(i))))m=i;}
        auto* ttl=cJSON_GetObjectItemCaseSensitive(req,"ttl");
        if(!cJSON_IsNumber(ttl)||ttl->valuedouble<1||ttl->valuedouble>300||ttl->valuedouble!=ttl->valueint)return "invalid_ttl";
        if(cJSON_HasObjectItem(req,"vitality")){auto* value=cJSON_GetObjectItemCaseSensitive(req,"vitality");if(!cJSON_IsNumber(value)||value->valuedouble<0||value->valuedouble>4||value->valuedouble!=value->valueint)return "invalid_vitality";v=value->valueint;}
        if(!avatar.set(node::Activity(a),node::Attention(t),node::Mood(m),v,ttl->valueint,now))return "invalid_display_state";
        random_expression.stop();
    }else if(profile){const char* value=text("profile");if(strcmp(value,"doom-calm")&&strcmp(value,"doom-injury-test"))return "invalid_profile";injury_profile=!strcmp(value,"doom-injury-test");}
    else if(!strcmp(op,"display_random")){random_expression.start(now,avatar_seed,avatar);}
    else if(!strcmp(op,"display_demo")){random_expression.stop();avatar.set(node::Activity::Idle,node::Attention::Calm,node::Mood::Neutral,-1,21,now);avatar.demo=true;}
    else {random_expression.stop();avatar=node::AvatarState{};}
    auto running_mission=mission_snapshot();if(running_mission.config.run)mission_apply(running_mission.config,false,0);
    world_view=false;mission_view=false;avatar_view=true;last_frame=0;return nullptr;
}
bool display_init() {
    world_runtime.start(esp_timer_get_time()/1000);
    uint8_t mac[6]{};esp_efuse_mac_get_default(mac);for(auto byte:mac)avatar_seed=avatar_seed*33+byte;
    Hub75Config cfg{};
    cfg.panel_width=64; cfg.panel_height=64;
    cfg.pins={4,5,6,7,15,16,18,8,3,42,9,40,2,41};
    cfg.brightness=node::brightness(25);
    cfg.double_buffer=true;
    cfg.output_clock_speed=Hub75ClockSpeed::HZ_10M;
    panel=new Hub75Driver(cfg); panel_ok=panel && panel->begin();
    gpio_config_t button{}; button.pin_bit_mask=1ULL; button.mode=GPIO_MODE_INPUT;
    button.pull_up_en=GPIO_PULLUP_ENABLE; gpio_config(&button);
    return panel_ok;
}
void display_next_page() { if(avatar_view){avatar_view=false;page=0;}else page=(page+1)%6; last_page=esp_timer_get_time()/1000; }
void display_tick(const char* label,bool memory_ok) {
    uint32_t now=esp_timer_get_time()/1000;
    auto mission=mission_snapshot();
    if(mission.config.run!=displayed_run){displayed_run=mission.config.run;world_view=false;mission_view=true;avatar_view=true;}
    world_index=(label[1]-'1')*4+label[0]-'A';if(world_index<0||world_index>=16)world_index=0;
    random_expression.tick(now,avatar);
    avatar.expire(now);
    int button=gpio_get_level(GPIO_NUM_0);
    if(!button && previous_button && now-last_press>200) { display_next_page(); presses++; last_press=now; }
    if(!button && now-last_press>=1000 && !long_press_fired) { audio_tone(); long_press_fired=true; }
    if(button) long_press_fired=false;
    previous_button=button;
    if(!avatar_view && now-last_page>=60000)avatar_view=true;
#ifdef FLOCK_PATTERNFLOW_TRIAL
    if(!panel_ok || now-last_frame<33) return;
    last_frame=now;
    uint64_t trial_begin=esp_timer_get_time();
    patternflow_trial::render(frame,now,world_index);
    ripples_draw(frame,now);
    panel->draw_pixels(0,0,64,64,reinterpret_cast<const uint8_t*>(frame.pixels),Hub75PixelFormat::RGB565,Hub75ColorOrder::RGB,false);
    panel->flip_buffer(); rendered++; last_duration_us=esp_timer_get_time()-trial_begin; return;
#endif
    if(!panel_ok || now-last_frame<125) return;
    if(last_frame && now-last_frame>250)dropped+=(now-last_frame)/125-1;
    last_frame=now;uint64_t begin=esp_timer_get_time();
    observed_warning=now>10000 && (!memory_ok || !sensors.sht_ok || !sensors.imu_ok || (!strcmp(storage_state(),"FAIL") || !strcmp(storage_state(),"UNRESPONSIVE")));
    if(avatar_view&&world_view){
        world_sample=survey_runtime.active?survey_runtime.sample(now):world_runtime.sample(now,world_index);
        if(survey_runtime.active)survey::render(frame,survey_runtime,now,world_sensor);
        else world::render(frame,world_sample,world_index,world_sensor);
        if(observed_warning){recon::Painter p{frame};p.rect(1,1,48,7,0);p.text(2,2,"HW WARNING",recon::warn);}
        if(maintenance_storage_busy())frame.text(18,1,"SD",1,0xffe0);
        panel->draw_pixels(0,0,64,64,reinterpret_cast<const uint8_t*>(frame.pixels),Hub75PixelFormat::RGB565,Hub75ColorOrder::RGB,false);
        panel->flip_buffer();rendered++;last_duration_us=esp_timer_get_time()-begin;
        world_timings[world_count++%256]=last_duration_us;world_max_us=std::max(world_max_us,last_duration_us);return;
    }
    if(avatar_view&&mission_view){
        int index=(label[1]-'1')*4+label[0]-'A';if(index<0||index>=16)index=0;
        world_sample=mission_world::render(frame,recon_scratch,mission,now,index);
        if(observed_warning){recon::Painter p{frame};p.rect(1,1,48,7,0);p.text(2,2,"HW WARNING",recon::warn);}
        if(maintenance_storage_busy())frame.text(18,1,"SD",1,0xffe0);
        panel->draw_pixels(0,0,64,64,reinterpret_cast<const uint8_t*>(frame.pixels),Hub75PixelFormat::RGB565,Hub75ColorOrder::RGB,false);
        panel->flip_buffer();rendered++;last_duration_us=esp_timer_get_time()-begin;
        world_timings[world_count++%256]=last_duration_us;world_max_us=std::max(world_max_us,last_duration_us);return;
    }
    if(avatar_view){
        auto current=effective(now);auto visual=current;
        if(observed_warning)visual=node::AvatarState{};
        unsigned index=node::avatar_frame(visual,now,avatar_seed,injury_profile);
        node::avatar_render(frame,face_media_frame(index),label,current,now,avatar_seed,observed_warning,network_connected(),network_peer_recent(),face_media_cached());
        if(maintenance_storage_busy())frame.text(18,1,"SD",1,0xffe0);
        panel->draw_pixels(0,0,64,64,reinterpret_cast<const uint8_t*>(frame.pixels),Hub75PixelFormat::RGB565,Hub75ColorOrder::RGB,false);
        panel->flip_buffer();rendered++;last_duration_us=esp_timer_get_time()-begin;return;
    }
    char l[5][16]{}; const char* lines[]={l[0],l[1],l[2],l[3],l[4]};
    const char* title="OVERVIEW";
    if(page==0) {
        snprintf(l[0],16,"RAM %s",memory_ok?"PASS":"FAIL");
        snprintf(l[1],16,"SHT %s",sensors.sht_ok?"PASS":"FAIL");
        snprintf(l[2],16,"IMU %s",sensors.imu_ok?"PASS":"WAIT");
        snprintf(l[3],16,"VISUAL PENDING"); snprintf(l[4],16,"PRESS BOOT NEXT");
    } else if(page==1) {
        title="SENSORS";
        if(sensors.sht_ok) { snprintf(l[0],16,"TEMP %.1f C",sensors.temperature); snprintf(l[1],16,"RH %.1f %%",sensors.humidity); }
        else snprintf(l[0],16,"SHT NO READING");
        snprintf(l[2],16,"IMU %s",sensors.imu_ok?"LIVE":"WAIT");
        snprintf(l[3],16,"RTC %s",sensors.rtc_advancing?"TICK":"WAIT");
        snprintf(l[4],16,"TIME %s",sensors.rtc_valid?"UNVERIFIED":"UNSET");
    } else if(page==2) {
        title="PERIPHERALS";
        snprintf(l[0],16,"PANEL CHECK ME"); snprintf(l[1],16,"SOUND CHECK ME");
        snprintf(l[2],16,"SD %.10s",storage_state()); snprintf(l[3],16,"WIFI %s",network_connected()?"LINK":"WAIT"); snprintf(l[4],16,"PEER %s",network_peer_recent()?"REPLY":"WAIT");
    }
    if(page==4) {
        title="AUDIO"; snprintf(l[0],16,"MIC %s",audio_ready()?"CAPTURE":"WAIT");
        snprintf(l[1],16,"M1 RMS %.0f",audio_level(0)); snprintf(l[2],16,"M2 RMS %.0f",audio_level(1));
        snprintf(l[3],16,"SOUND CHECK ME"); snprintf(l[4],16,"HOLD BOOT SOUND");
    } else if(page==5) {
        title="RADIO"; snprintf(l[0],16,"WIFI %s",network_connected()?"LINK":"WAIT");
        network_ip(l[1],16); snprintf(l[2],16,"CHANNEL %u",network_channel());
        snprintf(l[3],16,"PEER %s",network_peer_recent()?"REPLY":"WAIT"); snprintf(l[4],16,"SD %.10s",storage_state());
    }
    node::dashboard(frame,label,title,lines);
    if(page==3) {
        uint32_t t=now-last_page; int phase=(t/1500)%8;
        uint16_t color[]={0xf800,0x07e0,0x001f,0xffff,0,0,0,0}; frame.clear(color[phase]);
        if(phase==5) for(int y=0;y<64;y++) for(int x=0;x<64;x++) frame.pixel(x,y,((x+y)&1)?0xffff:0);
        if(phase==6) for(int i=0;i<64;i++) { frame.pixel((t/40)%64,i,0x07ff); frame.pixel(i,(t/40)%64,0xf81f); }
        if(phase==7) { frame.text(0,0,"TL",1,0xf800); frame.text(56,0,"TR",1,0x07e0); frame.text(0,59,"BL",1,0x001f); frame.text(56,59,"BR",1,0xffff); }
        // Full-field portion exposes pixels hidden by identity text.
        if(t%1500>1000 && phase!=7) frame.text(3,2,label,2,phase==3?0:0xffff);
    }
    panel->draw_pixels(0,0,64,64,reinterpret_cast<const uint8_t*>(frame.pixels),Hub75PixelFormat::RGB565,Hub75ColorOrder::RGB,false);
    panel->flip_buffer();
}
void display_json(cJSON* root) {
    auto* j=cJSON_AddObjectToObject(root,"panel");
    cJSON_AddStringToObject(j,"driver",panel_ok?"PASS":"FAIL");
    cJSON_AddStringToObject(j,"visual_acceptance","PENDING");
    cJSON_AddNumberToObject(j,"width",64); cJSON_AddNumberToObject(j,"height",64);
    cJSON_AddNumberToObject(j,"brightness_percent",25);
    cJSON_AddNumberToObject(j,"brightness_cap_percent",50);
#ifdef FLOCK_PATTERNFLOW_TRIAL
    cJSON_AddStringToObject(j,"view","patternflow-playlist");
    cJSON_AddStringToObject(j,"source","Patternflow ae1e3df; independent random playlist");
    cJSON_AddNumberToObject(j,"rendered_frames",rendered);
    cJSON_AddNumberToObject(j,"last_render_us",last_duration_us);
    cJSON_AddBoolToObject(j,"audio_coupling",false);
    cJSON_AddStringToObject(j,"pattern",patternflow_trial::patterns[patternflow_trial::current].name);
    cJSON_AddNumberToObject(j,"pattern_count",patternflow_trial::count);
    cJSON_AddNumberToObject(j,"pattern_changes",patternflow_trial::changes);
    return;
#endif

    cJSON_AddNumberToObject(j,"button_presses",presses);
    cJSON_AddNumberToObject(j,"page",page); cJSON_AddBoolToObject(j,"layout_clipped",frame.clipped);
    uint32_t now=esp_timer_get_time()/1000;auto state=effective(now);bool active=state.active(now);
    cJSON_AddStringToObject(j,"view",avatar_view?(world_view?"world":mission_view?"mission":"avatar"):"diagnostics");
    cJSON_AddStringToObject(j,"expression_mode",random_expression.enabled?"random":active?(state.demo?"sequential_demo":"override"):"auto");
    cJSON_AddNumberToObject(j,"random_expression_changes",random_expression.changes);
    cJSON_AddStringToObject(j,"profile",injury_profile?"doom-injury-test":"doom-calm");
    cJSON_AddStringToObject(j,"activity",node::activity_name(active?state.activity:node::Activity::Idle));
    cJSON_AddStringToObject(j,"attention",node::attention_name(active?state.attention:node::Attention::Calm));
    cJSON_AddStringToObject(j,"mood",node::mood_name(active?state.mood:node::Mood::Neutral));
    cJSON_AddStringToObject(j,"source",avatar_view&&mission_view&&!world_view?"scripted_mission_shared_world":avatar_view&&world_view?(survey_runtime.active?"host_fictional_survey":"synthetic_local_world"):active?(state.demo?"demo":"experiment"):"observed");
    cJSON_AddStringToObject(j,"health",now<10000?"unknown":observed_warning?"degraded":"nominal");
    cJSON_AddStringToObject(j,"health_reasons",observed_warning?"inspect PSRAM, SHT, IMU and SD diagnostic results":"none observed in monitored checks");
    cJSON_AddStringToObject(j,"health_scope","PSRAM, SHT, IMU, SD local checks; manual acceptance separate");
    cJSON_AddNumberToObject(j,"override_remaining_ms",state.remaining(now));
    cJSON_AddNumberToObject(j,"experimental_vitality",active?state.vitality:-1);
    cJSON_AddNumberToObject(j,"ambient_seed",avatar_seed);
    cJSON_AddNumberToObject(j,"rendered_frames",rendered);cJSON_AddNumberToObject(j,"dropped_frames",dropped);
    cJSON_AddNumberToObject(j,"last_render_us",last_duration_us);
    auto* w=cJSON_AddObjectToObject(j,"world");
    cJSON_AddNumberToObject(w,"version",1);cJSON_AddNumberToObject(w,"seed",world::Seed);
    cJSON_AddNumberToObject(w,"elapsed_ms",avatar_view&&mission_view&&!world_view?world_sample.time:world_runtime.elapsed);cJSON_AddStringToObject(w,"sensor",world::sensor_name(world_sensor));
    cJSON_AddStringToObject(w,"source",avatar_view&&mission_view&&!world_view?"scripted_mission_shared_world":survey_runtime.active?"host_fictional_survey":"local_authored_fixture");cJSON_AddStringToObject(w,"peer_source",survey_runtime.active?"host_simulated_peers":"synthetic_not_network_observations");
    auto* survey=cJSON_AddObjectToObject(j,"survey");const auto& packet=survey_runtime.latest;
    cJSON_AddBoolToObject(survey,"active",survey_runtime.active&&world_view);
    cJSON_AddNumberToObject(survey,"run",packet.run);cJSON_AddNumberToObject(survey,"seq",packet.seq);
    cJSON_AddNumberToObject(survey,"time_ms",packet.time);cJSON_AddNumberToObject(survey,"age_ms",survey_runtime.seen?uint32_t(now-survey_runtime.received):0);
    cJSON_AddStringToObject(survey,"state",survey::States[packet.state]);cJSON_AddNumberToObject(survey,"energy",packet.energy);
    cJSON_AddNumberToObject(survey,"distance_units",packet.distance);cJSON_AddNumberToObject(survey,"reserve",packet.reserve);
    cJSON_AddNumberToObject(survey,"peer_count",packet.peerCount);
    cJSON_AddStringToObject(w,"stage",world::stage_name(world_sample.stage));
    cJSON_AddStringToObject(w,"freshness",world_sample.freshness==world::Stale?"STALE":world_sample.freshness==world::Resync?"RESYNC":"LIVE");
    cJSON_AddBoolToObject(w,"paused",world_runtime.paused);cJSON_AddBoolToObject(w,"updates_enabled",world_runtime.enabled);
    auto* pos=cJSON_AddArrayToObject(w,"position");for(float n:{world_sample.pose.position.x,world_sample.pose.position.y,world_sample.pose.position.z})cJSON_AddItemToArray(pos,cJSON_CreateNumber(n));
    cJSON_AddNumberToObject(w,"heading",world_sample.pose.heading);
    uint32_t sorted[256];unsigned count=std::min<uint32_t>(world_count,256);std::copy(world_timings,world_timings+count,sorted);std::sort(sorted,sorted+count);
    cJSON_AddNumberToObject(w,"render_samples",count);cJSON_AddNumberToObject(w,"render_p50_us",count?sorted[(count-1)/2]:0);
    cJSON_AddNumberToObject(w,"render_p95_us",count?sorted[(count*95+99)/100-1]:0);cJSON_AddNumberToObject(w,"render_max_us",world_max_us);
    cJSON_AddStringToObject(j,"experiment_traffic","UNAVAILABLE");
    face_media_json(root);mission_json(root);
}
