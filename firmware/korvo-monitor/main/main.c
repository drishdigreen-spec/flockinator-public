#include <inttypes.h>
#include "bsp/display.h"
#include "bsp/button.h"
#include "bsp/led.h"
#include "freertos/queue.h"
#include "controls.h"
#include "feedback.h"
#include "lab_host.h"
#include "controller.h"
#include "driver/uart.h"
#include "esp_mac.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "telemetry.h"

static lv_obj_t *tiles[16], *captions[16], *detail, *summary, *node_title, *node_state;
static telemetry_t nodes[16];
static uint64_t received[16];
static bool seen[16];
static unsigned selected;
static lv_obj_t *mission_panel,*map_nodes[16],*map_status,*mission_result,*scenario_label,*goal_label,*duration_label,*repeat_label;
static int32_t map_x[16],map_y[16];
static uint64_t map_time[16];
static bool map_seen[16], event_seen[16];
static unsigned map_state[16];
static uint64_t last_cue;
static unsigned scenario,goal,duration=64,repeat=1,mission_id;
static bool mission_pending;
static uint64_t mission_deadline;
static controls_t controls = {.volume=50};
static lv_obj_t *settings_panel, *blank_panel, *volume_label, *sound_status, *mute_label;
static QueueHandle_t actions;
static bool sound_ready;
static button_handle_t hardware_buttons[BSP_BUTTON_NUM];
static const char *states[] = {"NO RESPONSE", "LIVE", "ERROR", "STALE", "WAITING"};
static const uint32_t colors[] = {0x62452d, 0x245f60, 0x713541, 0x625529, 0x293b4b};
static const char *map_states[] = {"NO DATA", "LIVE", "ERROR", "STALE", "WAITING"};
static lv_obj_t *lab_panel,*lab_info,*lab_url,*lab_score,*lab_tiles[16];
static void refresh(uint64_t now);
static void lab_show(lv_event_t* event) {
    lv_obj_set_hidden(lab_panel,lv_event_get_user_data(event)==NULL);
}
static void lab_button(lv_obj_t* parent,const char* title,int x,int y,void* open){
    lv_obj_t* b=lv_button_create(parent);
    lv_obj_set_pos(b,x,y);lv_obj_set_size(b,146,40);
    lv_obj_add_event_cb(b,lab_show,LV_EVENT_CLICKED,open);
    lv_obj_t* l=lv_label_create(b);lv_label_set_text(l,title);lv_obj_center(l);
}

static void select_node(lv_event_t *event)
{
    selected = (unsigned)(uintptr_t)lv_event_get_user_data(event);
    feedback_play(controls.muted ? 0 : controls.volume, 880);
    refresh((uint64_t)(esp_timer_get_time()/1000));
    ESP_LOGI("monitor", "selected=%c%u", 'A' + selected/4, selected%4+1);
}
static lv_obj_t *label(lv_obj_t *parent, const char *text, int x, int y)
{
    lv_obj_t *item = lv_label_create(parent);
    lv_label_set_text(item, text);
    lv_obj_set_pos(item, x, y);
    lv_obj_set_style_text_font(item, &lv_font_montserrat_24, 0);
    lv_obj_set_style_text_color(item, lv_color_hex(0xffffff), 0);
    return item;
}
static lv_obj_t *small_label(lv_obj_t *parent, const char *text, int x, int y)
{
    lv_obj_t *item = label(parent, text, x, y);
    lv_obj_set_style_text_font(item, &lv_font_montserrat_14, 0);
    lv_obj_set_style_text_color(item, lv_color_hex(0xa7bbc9), 0);
    return item;
}
static void refresh(uint64_t now)
{
    unsigned counts[5] = {0};
    for (unsigned i=0; i<16; i++) {
        unsigned state = seen[i] ? telemetry_state(nodes[i].state, received[i], now) : 4;
        counts[state]++;
        lv_obj_set_style_bg_color(tiles[i], lv_color_hex(colors[state]), 0);
        lv_obj_set_style_border_width(tiles[i], i == selected ? 3 : 0, 0);
        lv_obj_set_style_border_color(tiles[i], lv_color_hex(0xffffff), 0);
        lv_label_set_text(captions[i], map_states[state]);
    }
    lv_label_set_text_fmt(summary, "%u LIVE   %u NO REPLY   %u ERROR\n%u STALE   %u WAITING",
        counts[1], counts[0], counts[2], counts[3], counts[4]);
    unsigned state = seen[selected] ? telemetry_state(nodes[selected].state, received[selected], now) : 4;
    lv_label_set_text_fmt(node_title, "Panel %c%u", 'A'+selected/4, selected%4+1);
    lv_label_set_text(node_state, states[state]);
    lv_obj_set_style_bg_color(node_state, lv_color_hex(colors[state]), 0);
    if (seen[selected] && nodes[selected].state == 1) {
        uint32_t uptime = nodes[selected].uptime;
        lv_label_set_text_fmt(detail, "Firmware  %s\n\nUptime  %" PRIu32 "h %" PRIu32 "m\nFree RAM  %" PRIu32 " KiB\n\nReading age  %llu s",
            nodes[selected].version, uptime/3600, uptime/60%60, nodes[selected].ram,
            (unsigned long long)((now-received[selected])/1000));
    } else {
        lv_label_set_text(detail,
            state == 0 ? "No response to the\nlatest status request.\n\nPower or network may\nbe unavailable." :
            state == 2 ? "Status could not be\nvalidated.\n\nCheck the host bridge\nfor access or identity\nerrors." :
            state == 3 ? "Telemetry has expired.\n\nCheck the host bridge\nand USB connection." :
            "Waiting for a fresh\nstatus report.");
    }
}
static void create_overview(lv_obj_t *screen)
{
    lv_obj_set_style_bg_color(screen, lv_color_hex(0x101b25), 0);
    lv_obj_set_scrollable(screen, false);
    label(screen, "FLEET OVERVIEW", 24, 16);
    small_label(screen, "PHYSICAL LAYOUT  /  A1-D4", 24, 49);
    summary = small_label(screen, "Waiting for telemetry", 430, 18);
    lv_obj_set_style_text_line_space(summary, 6, 0);

    /* Square panel map, row A at top and column 1 at left. No mission positions. */
    for (unsigned i=0; i<4; i++) {
        char axis[2] = {(char)('1'+i), 0};
        small_label(screen, axis, 88+i*84, 78);
        axis[0] = (char)('A'+i);
        small_label(screen, axis, 24, 132+i*84);
    }
    for (unsigned i=0; i<16; i++) {
        tiles[i] = lv_button_create(screen);
        lv_obj_set_pos(tiles[i], 54+(i%4)*84, 104+(i/4)*84);
        lv_obj_set_size(tiles[i], 76, 76);
        lv_obj_set_style_pad_all(tiles[i], 0, 0);
        lv_obj_set_style_radius(tiles[i], 8, 0);
        lv_obj_set_style_shadow_width(tiles[i], 0, 0);
        lv_obj_set_scrollable(tiles[i], false);
        lv_obj_add_event_cb(tiles[i], select_node, LV_EVENT_CLICKED, (void *)(uintptr_t)i);
        char name[3] = {(char)('A'+i/4), (char)('1'+i%4), 0};
        lv_obj_t *id = label(tiles[i], name, 0, 0);
        lv_obj_align(id, LV_ALIGN_TOP_MID, 0, 10);
        captions[i] = small_label(tiles[i], "WAITING", 0, 0);
        lv_obj_set_style_text_color(captions[i], lv_color_hex(0xffffff), 0);
        lv_obj_align(captions[i], LV_ALIGN_BOTTOM_MID, 0, -10);
    }
    lv_obj_t *inspector = lv_obj_create(screen);
    lv_obj_set_pos(inspector, 418, 84);
    lv_obj_set_size(inspector, 358, 348);
    lv_obj_set_style_bg_color(inspector, lv_color_hex(0x192a37), 0);
    lv_obj_set_style_border_width(inspector, 0, 0);
    lv_obj_set_style_radius(inspector, 12, 0);
    lv_obj_set_style_pad_all(inspector, 20, 0);
    lv_obj_set_scrollable(inspector, false);
    node_title = label(inspector, "Panel A1", 0, 0);
    lv_obj_set_style_text_font(node_title, &lv_font_montserrat_32, 0);
    node_state = small_label(inspector, "WAITING", 0, 50);
    lv_obj_set_style_text_color(node_state, lv_color_hex(0xffffff), 0);
    lv_obj_set_style_bg_opa(node_state, LV_OPA_COVER, 0);
    lv_obj_set_style_pad_all(node_state, 6, 0);
    lv_obj_set_style_radius(node_state, 4, 0);
    detail = label(inspector, "Waiting for telemetry", 0, 96);
    lv_obj_set_style_text_font(detail, &lv_font_montserrat_18, 0);
    lv_obj_set_width(detail, 318);
    lv_obj_set_style_text_line_space(detail, 4, 0);
    small_label(screen, "Tap a panel to inspect", 54, 452);

    refresh(0);
    lv_obj_update_layout(screen);
    /* Check real LVGL text sizes, including the longest tile state, on hardware. */
    int32_t widest = 0;
    for (unsigned i=0; i<16; i++) {
        for (unsigned state=0; state<5; state++) {
            lv_label_set_text(captions[i], map_states[state]);
            lv_obj_update_layout(tiles[i]);
            int32_t width = lv_obj_get_width(captions[i]);
            if (width > widest) widest = width;
        }
    }
    refresh(0);
    lv_obj_update_layout(screen);
    int32_t detail_height = lv_obj_get_height(detail);
    ESP_LOGI("monitor", "overview_layout=%s; tile=76x76; status_width=%ld; detail_height=%ld",
        widest <= 70 && detail_height <= 212 ? "PASS" : "OVERFLOW",
        (long)widest, (long)detail_height);
}

/* Called with the LVGL lock held, either by LVGL or the UART/main task. */
static void apply_control(control_action_t action)
{
    controls_apply(&controls, action);
    if (action == CONTROL_HOME) {selected=0;lv_obj_set_hidden(mission_panel,true);lv_obj_set_hidden(lab_panel,true);}
    lv_obj_set_hidden(settings_panel, !controls.settings);
    lv_obj_set_hidden(blank_panel, !controls.sleeping);
    lv_label_set_text_fmt(volume_label, "Volume  %d%%", controls.volume);
    lv_label_set_text(mute_label, controls.muted ? "Unmute" : "Mute");
    lv_label_set_text_fmt(sound_status, "%s  %d%%", !sound_ready ? "Audio unavailable" : controls.muted ? "Muted" : "Sound", controls.volume);
    if(action == CONTROL_TEST) feedback_event(controls.muted || controls.sleeping ? 0 : controls.volume,940,2);
    else feedback_play(controls.muted || controls.sleeping ? 0 : controls.volume,1040);
    refresh((uint64_t)(esp_timer_get_time()/1000));
    ESP_LOGI("controls", "action=%d volume=%d muted=%d sleeping=%d settings=%d",
        action,controls.volume,controls.muted,controls.sleeping,controls.settings);
}
static void touch_control(lv_event_t *event)
{
    apply_control((control_action_t)(uintptr_t)lv_event_get_user_data(event));
}
static lv_obj_t *control_button(lv_obj_t *parent, const char *text, int x, int y,
                               int width, control_action_t action)
{
    lv_obj_t *button=lv_button_create(parent);
    lv_obj_set_pos(button,x,y); lv_obj_set_size(button,width,54);
    lv_obj_set_style_bg_color(button,lv_color_hex(0x245f60),0);
    lv_obj_add_event_cb(button,touch_control,LV_EVENT_CLICKED,(void *)(uintptr_t)action);
    lv_obj_t *caption=label(button,text,0,0);
    lv_obj_center(caption);
    return caption;
}
static void create_mission(lv_obj_t *screen);
static void create_controls(lv_obj_t *screen)
{
    sound_status=small_label(screen,sound_ready ? "Sound 50%" : "Audio unavailable",270,452);
    lv_obj_t *open=control_button(screen,"Settings",650,434,126,CONTROL_SETTINGS);
    lv_obj_set_height(lv_obj_get_parent(open),44);
    lv_obj_set_style_text_font(open,&lv_font_montserrat_18,0);
    create_mission(screen);
    lab_button(screen,"Learning lab",350,434,(void*)1);
    lab_panel=lv_obj_create(screen);
    lv_obj_set_pos(lab_panel,0,0);lv_obj_set_size(lab_panel,800,480);
    lv_obj_set_scrollable(lab_panel,false);
    lv_obj_set_style_bg_color(lab_panel,lv_color_hex(0x101b25),0);
    label(lab_panel,"COMMUNICATION LAB",14,4);
    lab_info=small_label(lab_panel,"Starting world",14,50);
    lab_score=label(lab_panel,"",390,95);
    lab_url=small_label(lab_panel,"Joining Wi-Fi",390,300);
    for(int i=0;i<16;i++){
        lv_obj_t* tile=lv_label_create(lab_panel);lab_tiles[i]=tile;
        lv_label_set_text_fmt(tile,"%c%d",'A'+i%4,i/4+1);
        lv_obj_set_pos(tile,18+(i%4)*82,90+(i/4)*68);lv_obj_set_size(tile,70,54);
        lv_obj_set_style_bg_opa(tile,LV_OPA_COVER,0);lv_obj_set_style_pad_all(tile,12,0);
        lv_obj_set_style_text_color(tile,lv_color_hex(0xffffff),0);
    }
    small_label(lab_panel,"Green: both correct   Amber: clear only   Blue: altered only   Red: both missed",14,370);
    lab_button(lab_panel,"Fleet overview",560,390,NULL);
    settings_panel=lv_obj_create(screen);
    lv_obj_set_pos(settings_panel,0,0); lv_obj_set_size(settings_panel,800,480);
    lv_obj_set_style_bg_color(settings_panel,lv_color_hex(0x101b25),0);
    lv_obj_set_style_bg_opa(settings_panel,LV_OPA_COVER,0);
    lv_obj_set_style_pad_all(settings_panel,0,0);
    lv_obj_set_style_border_width(settings_panel,0,0);
    lv_obj_set_style_radius(settings_panel,0,0);
    lv_obj_set_scrollable(settings_panel,false);
    label(settings_panel,"SOUND & DISPLAY",32,28);
    small_label(settings_panel,"Touch controls are always available here",32,70);
    volume_label=label(settings_panel,"Volume 50%",32,118);
    control_button(settings_panel,"Volume -",32,170,220,CONTROL_DOWN);
    control_button(settings_panel,"Volume +",272,170,220,CONTROL_UP);
    mute_label=control_button(settings_panel,"Mute",512,170,256,CONTROL_MUTE);
    control_button(settings_panel,"Test sound",32,246,220,CONTROL_TEST);
    control_button(settings_panel,"Screen sleep",272,246,220,CONTROL_SLEEP);
    control_button(settings_panel,"Back to fleet",512,246,256,CONTROL_HOME);
    small_label(settings_panel,"Tap the sleeping screen to wake. Monitoring continues.",32,326);
    small_label(settings_panel,"Buttons: VOL+ / VOL- / MODE: sleep / SET: home",32,360);
    small_label(settings_panel,"Screen sleep blanks the image; the backlight stays powered.",32,394);
    small_label(settings_panel,"Sound starts at 50% after restart. Mute stops interface tones.",32,428);
    lv_obj_set_hidden(settings_panel,true);
    blank_panel=lv_obj_create(screen);
    lv_obj_set_pos(blank_panel,0,0);lv_obj_set_size(blank_panel,800,480);
    lv_obj_set_style_bg_color(blank_panel,lv_color_hex(0),0);
    lv_obj_set_style_bg_opa(blank_panel,LV_OPA_COVER,0);
    lv_obj_set_style_border_width(blank_panel,0,0);
    lv_obj_set_style_radius(blank_panel,0,0);
    lv_obj_set_scrollable(blank_panel,false);
    lv_obj_add_event_cb(blank_panel,touch_control,LV_EVENT_CLICKED,(void *)(uintptr_t)CONTROL_WAKE);
    lv_obj_set_hidden(blank_panel,true);
}
static const char *scenarios[]={"Mixed outcomes","Survey and return","Link disruption"};
static const char *goals[]={"Observe","Compare reports","Recovery"};
static void mission_touch(lv_event_t *e)
{
    unsigned action=(unsigned)(uintptr_t)lv_event_get_user_data(e);
    ESP_LOGI("mission", "touch_action=%u", action);
    if(action==0) lv_obj_set_hidden(mission_panel,false);
    else if(action==1) scenario=(scenario+1)%3;
    else if(action==2) goal=(goal+1)%3;
    else if(action==3) duration=duration==64?96:64;
    else if(action==4) repeat=!repeat;
    else if(action==5 || action==6) {
        if(mission_pending) return;
        mission_pending=true; mission_deadline=(uint64_t)(esp_timer_get_time()/1000)+30000;
        mission_id++;
        if(standalone_ready()){
            bool ok=standalone_touch(action==5,scenario,goal,duration,repeat);
            mission_pending=false;lv_label_set_text(mission_result,ok?"Command queued locally":"Busy or command rejected");
            return;
        }
        printf("MC1 %u %u %u %u %u %u\n",mission_id,action==5,scenario,goal,duration,repeat);fflush(stdout);
        lv_label_set_text(mission_result,"Sending request...");
    } else if(action==7) lv_obj_set_hidden(mission_panel,true);
    lv_label_set_text_fmt(scenario_label,"Scenario: %s",scenarios[scenario]);
    lv_label_set_text_fmt(goal_label,"Goal: %s",goals[goal]);
    lv_label_set_text_fmt(duration_label,"Duration: %u s",duration);
    lv_label_set_text_fmt(repeat_label,"Repeat: %s",repeat?"on":"off");
    feedback_play(controls.muted?0:controls.volume,880);
}
static lv_obj_t *mission_button(lv_obj_t *parent,const char *text,int x,int y,int w,int h,unsigned action)
{
    lv_obj_t *b=lv_button_create(parent);lv_obj_set_pos(b,x,y);lv_obj_set_size(b,w,h);
    lv_obj_set_style_bg_color(b,lv_color_hex(0x245f60),0);
    lv_obj_add_event_cb(b,mission_touch,LV_EVENT_CLICKED,(void *)(uintptr_t)action);
    lv_obj_t *l=lv_label_create(b);lv_label_set_text(l,text);lv_obj_set_style_text_font(l,&lv_font_montserrat_14,0);lv_obj_center(l);return l;
}
static void create_mission(lv_obj_t *screen)
{
    mission_button(screen,"Missions",500,434,140,44,0);
    mission_panel=lv_obj_create(screen);lv_obj_set_pos(mission_panel,0,0);lv_obj_set_size(mission_panel,800,480);
    lv_obj_set_style_pad_all(mission_panel,0,0);lv_obj_set_style_border_width(mission_panel,0,0);lv_obj_set_style_radius(mission_panel,0,0);
    lv_obj_set_style_bg_color(mission_panel,lv_color_hex(0x101b25),0);lv_obj_set_scrollable(mission_panel,false);
    label(mission_panel,"MISSION / SCRIPTED WORLD",20,12);
    small_label(mission_panel,"Node-reported positions | north up",20,45);
    lv_obj_t *map=lv_obj_create(mission_panel);lv_obj_set_pos(map,20,72);lv_obj_set_size(map,400,352);
    lv_obj_set_style_pad_all(map,0,0);lv_obj_set_style_bg_color(map,lv_color_hex(0x253728),0);lv_obj_set_scrollable(map,false);
    for(unsigned i=0;i<16;i++){map_nodes[i]=lv_label_create(map);lv_label_set_text_fmt(map_nodes[i],"%c%u",'A'+i/4,i%4+1);lv_obj_set_style_text_font(map_nodes[i],&lv_font_montserrat_14,0);lv_obj_set_style_text_color(map_nodes[i],lv_color_hex(0x80dcf2),0);lv_obj_set_hidden(map_nodes[i],true);}
    map_status=small_label(mission_panel,"Waiting for world reports",20,434);
    scenario_label=mission_button(mission_panel,"Scenario: Mixed outcomes",440,72,340,48,1);
    goal_label=mission_button(mission_panel,"Goal: Observe",440,130,340,48,2);
    duration_label=mission_button(mission_panel,"Duration: 64 s",440,188,160,48,3);
    repeat_label=mission_button(mission_panel,"Repeat: on",610,188,170,48,4);
    mission_button(mission_panel,"START",440,250,160,54,5);
    mission_button(mission_panel,"STOP",610,250,170,54,6);
    mission_result=small_label(mission_panel,"Select parameters, then start",440,322);
    lv_obj_set_width(mission_result,330);
    small_label(mission_panel,"Green: SHARE   Red: ENGAGE/KILL",440,350);
    small_label(mission_panel,"Blue: FRIEND   Amber: SEEN/TARGET",440,370);
    mission_button(mission_panel,"Back to fleet",440,390,340,54,7);
    lv_obj_set_hidden(mission_panel,true);
}
static void update_map(uint64_t now)
{
    unsigned live=0;
    if(mission_pending && now>mission_deadline) {mission_pending=false;lv_label_set_text(mission_result,"Timed out; result unknown");}
    for(unsigned i=0;i<16;i++) {
        bool visible=map_seen[i] && now-map_time[i]<=20000 && map_x[i]>=-800 && map_x[i]<=2400 && map_y[i]>=-1000 && map_y[i]<=2100;
        lv_obj_set_hidden(map_nodes[i],!visible);
        if(visible){
            int x=map_x[i]/10, y=map_y[i]/10;
            uint32_t color=0x80dcf2;
            if(map_state[i]==3) color=(now/250)%2 ? 0x56ff80 : 0x166333;
            else if(map_state[i]==6 || map_state[i]==8) color=0xff5555;
            else if(map_state[i]==22) color=0x62a8ff;
            else if(map_state[i]==23 || map_state[i]==2) color=0xffc35c;
            else if(map_state[i]==9 || map_state[i]==7 || map_state[i]==11) color=0xb98286;
            lv_obj_set_style_text_color(map_nodes[i],lv_color_hex(color),0);
            lv_obj_set_pos(map_nodes[i],(x+80)*370/320, (210-y)*320/310);live++;
        }
    }
    lv_label_set_text_fmt(map_status,"%u fresh positions / 16 | scripted world",live);
}
static void hardware_control(void *button, void *arg)
{
    (void)button;
    control_action_t action=(control_action_t)(uintptr_t)arg;
    xQueueSend(actions,&action,0);
}
static void init_buttons(void)
{
    int count=0;
    actions=xQueueCreate(8,sizeof(control_action_t));
    if (!actions || bsp_iot_button_create(hardware_buttons,&count,BSP_BUTTON_NUM) != ESP_OK) {
        ESP_LOGE("controls","Hardware buttons unavailable; touch controls remain active"); return;
    }
    const control_action_t map[BSP_BUTTON_NUM]={CONTROL_UP,CONTROL_DOWN,CONTROL_SLEEP,CONTROL_HOME};
    for(int i=0;i<count;i++) {
        esp_err_t result=iot_button_register_cb(hardware_buttons[i],BUTTON_PRESS_DOWN,NULL,hardware_control,(void *)(uintptr_t)map[i]);
        if (result != ESP_OK) ESP_LOGE("controls","Button %d callback failed: %d",i,result);
    }
    ESP_LOGI("controls","buttons ready: VOLUP/VOLDOWN/MODE sleep/SET home");
}

static void start_lab_task(void* arg) { (void)arg;lab_start();vTaskDelete(NULL); }

void app_main(void)
{
    ESP_ERROR_CHECK(uart_driver_install(UART_NUM_0, 2048, 0, 0, NULL, 0));
    sound_ready=feedback_init();
    if (!bsp_display_start() || !bsp_display_lock(-1)) {
        ESP_LOGE("monitor", "Display initialization failed"); return;
    }
    create_overview(lv_screen_active());
    create_controls(lv_screen_active());
    bsp_display_unlock();
    init_buttons();
    xTaskCreate(start_lab_task,"lab_init",10240,NULL,2,NULL);
    bool led_ready = bsp_led_init() == ESP_OK;
    int led_state = -1;
    if (!led_ready) ESP_LOGE("controls", "Status LED unavailable");
    feedback_play(controls.volume,660);
    uint8_t mac[6]; ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_BASE));
    char line[256]; size_t used=0; bool discard=false;
    uint64_t next_refresh=0, next_map=0;
    while (true) {
        control_action_t action;
        while (actions && xQueueReceive(actions,&action,0)==pdTRUE) {
            if (bsp_display_lock(100)) {apply_control(action);bsp_display_unlock();}
        }
        uint8_t bytes[256];
        int count=uart_read_bytes(UART_NUM_0, bytes, sizeof(bytes), pdMS_TO_TICKS(50));
        uint64_t now=(uint64_t)(esp_timer_get_time()/1000);
        for (int j=0; j<count; j++) {
            if (bytes[j]=='\n') {
                line[used]=0; telemetry_t update;
                if(!discard && !strncmp(line,"LW1 ",4)){
                    printf("LW1 %s\n",lab_provision(line)?"OK":"REJECTED");
                    memset(line,0,sizeof(line));fflush(stdout);
                }
                if(!discard && !strncmp(line,"FK1 ",4)){
                    printf("FK1 %s\n",standalone_usb(line)?"OK":"REJECTED");
                    memset(line,0,sizeof(line));fflush(stdout);
                }
                if(!discard && !strcmp(line,"OP1 00:11:22:33:44:55")){
                    printf("OP1 %06u\n",standalone_pin());fflush(stdout);
                }
                unsigned ix,heading,fresh,running,state,rid,phase,ok,fail; int x,y; char extra;
                if (!discard && sscanf(line,"P2 %u %d %d %u %u %u %u %c",&ix,&x,&y,&heading,&fresh,&running,&state,&extra)==7 && ix<16 && heading<=360 && fresh<=2 && running<=1 && state<30 && x>=-1000000 && x<=1000000 && y>=-1000000 && y<=1000000 && bsp_display_lock(100)) {
                    if (fresh && running && event_seen[ix] && now-map_time[ix]<=20000 && map_state[ix]!=state && now-last_cue>=3000 && !controls.sleeping) {
                        int hz=0;
                        switch(state) {case 27: hz=740;break;case 2: hz=940;break;case 22: hz=620;break;
                            case 23: hz=1060;break;case 6: hz=1180;break;case 15: hz=820;break;
                            case 3: hz=700;break;case 18: hz=520;break;case 9: case 8: hz=300;break;}
                        if(hz && !controls.muted && controls.volume) {feedback_event(controls.volume,hz,state);last_cue=now;}
                    }
                    map_state[ix]=state;event_seen[ix]=fresh && running;
                    map_x[ix]=x;map_y[ix]=y;map_time[ix]=now;map_seen[ix]=fresh!=0;bsp_display_unlock();
                }
                if (!discard && sscanf(line,"R1 %u %u %u %u %c",&rid,&phase,&ok,&fail,&extra)==4 && rid==mission_id && phase<=1 && ok<=16 && fail<=16 && bsp_display_lock(100)) {
                    if(phase) {mission_pending=false;lv_label_set_text_fmt(mission_result,"Verified: %u   Failed: %u",ok,fail);}
                    else lv_label_set_text(mission_result,"Sending to fleet...");
                    bsp_display_unlock();
                }
                if (!discard && telemetry_parse(line, &update) && bsp_display_lock(100)) {
                    nodes[update.index]=update; received[update.index]=now; seen[update.index]=true;
                    bsp_display_unlock();
                    ESP_LOGI("monitor", "received=%u state=%u", update.index, update.state);
                }
                used=0; discard=false;
            } else if (bytes[j]=='\r') { /* Accept CRLF. */
            } else if (bytes[j] == 0 || used == sizeof(line)-1) { discard=true;
            } else if (!discard) line[used++]=(char)bytes[j];
        }
        if (now >= next_map) {
            if (bsp_display_lock(100)) {
                if(standalone_ready())for(int i=0;i<16;i++){
                    panel_view_t p;standalone_panel(i,&p);
                    if(p.known){nodes[i].index=i;nodes[i].state=p.live?1:0;nodes[i].uptime=p.uptime;nodes[i].ram=p.ram;snprintf(nodes[i].version,sizeof(nodes[i].version),"%s",p.version);received[i]=now-p.age_ms;seen[i]=true;}
                    map_x[i]=p.x*10;map_y[i]=p.y*10;map_state[i]=p.state;map_time[i]=now;map_seen[i]=p.running;
                }
                update_map(now);bsp_display_unlock();
            }
            next_map=now+250;
        }
        if (now >= next_refresh) {
            int next_led = 1;
            for (unsigned i=0; i<16; i++) {
                unsigned state=seen[i] ? telemetry_state(nodes[i].state, received[i], now) : 4;
                if (state==0 || state==2) {next_led=2; break;}
                if (state==3 || state==4) next_led=0;
            }
            if (led_ready && next_led != led_state) {
                const uint8_t rgb[3][3]={{8,4,0},{0,8,3},{10,1,0}};
                esp_err_t result=bsp_led_set_rgb(BSP_LED_STATUS,rgb[next_led][0],rgb[next_led][1],rgb[next_led][2]);
                if (result == ESP_OK) {led_state=next_led; ESP_LOGI("controls", "fleet_led=%d",led_state);}
                else ESP_LOGE("controls", "Status LED update failed: %d",result);
            }
            if (bsp_display_lock(100)) {
                refresh(now);
                lab_metrics_t m;lab_metrics(&m);
                lv_label_set_text_fmt(lab_info,"%s   |   seed %u   |   step %u / 80",m.paused?"PAUSED":m.turn==80?"COMPLETE":m.turn<48?"TRAINING":"TESTING",m.seed,m.turn);
                lv_label_set_text_fmt(lab_score,"Recoveries\n\nClear       %d\nAltered    %d\nSolo         %d",m.clear,m.altered,m.solo);
                if(m.ip[0])printf("LAB1 %s\n",m.ip);
                lv_label_set_text_fmt(lab_url,"Web controls\n%s%s\nOperator PIN %06u",m.ip[0]?"http://":"",m.ip[0]?m.ip:"Waiting for Wi-Fi",standalone_pin());
                const uint32_t palette[]={0x355166,0x24684f,0x886428,0x305d88,0x80434b};
                for(int i=0;i<16;i++)lv_obj_set_style_bg_color(lab_tiles[i],lv_color_hex(palette[m.correct[i]]),0);
                bsp_display_unlock();
            }
            printf("KORVO1 %02X:%02X:%02X:%02X:%02X:%02X\n", mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
            fflush(stdout); next_refresh=now+1000;
        }
    }
}
