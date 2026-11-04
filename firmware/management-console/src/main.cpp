#include <Arduino.h>
#include "epd_driver.h"
#include "roboto18.h"
#include "roboto12.h"
#include "console_ui.h"
#include "live_link.h"
#include "refresh_policy.h"
#include "refresh_regions.h"
#include "touch_events.h"

using namespace flockinator;
namespace {
Console console;
RefreshPolicy refresh_policy;
uint32_t last_live_render = 0;
bool dirty = true;
bool full_requested = false;
Page displayed_page = Page::Overview;
bool sleep_requested = false;
bool button_held = false;
uint32_t button_started = 0;
uint32_t last_poll = 0;
uint32_t last_render = 0;

struct EpaperCanvas {
    void rect(Rect box, bool fill, uint8_t shade = 0) {
        if (fill) epd_fill_rect(box.x, box.y, box.w, box.h, shade, screen_buffer());
        else epd_draw_rect(box.x, box.y, box.w, box.h, shade, screen_buffer());
    }
    void text(int x, int y, const char* value, int size = 18) {
        // Vendor names are point sizes: Roboto18 ascends 35 pixels, Roboto12 24.
        const GFXfont* font = size == 32 ? &Roboto18 : &Roboto12;
        int32_t cursor_x = x, cursor_y = y;
        writeln(font, value, &cursor_x, &cursor_y, screen_buffer());
    }
};

void apply(Action action) {
    if (action != Action::None) dirty = true;
    if (action == Action::Refresh) full_requested = true;
    if(action==Action::MissionStart||action==Action::MissionStop){auto config=console.draft;config.run=0;config.seed=0;live_mission(config,action==Action::MissionStart);}
    if (action == Action::Deploy) live_deploy_selected(console.selected);
    if (action == Action::Sleep) {
        if (live_can_sleep()) sleep_requested = true;
        else { console.page = Page::Detail; dirty = true; }
    }
}

void select_button(int index) {
    const Rect box = button_rect(index);
    apply(console.tap({box.x + 2, box.y + 2}));
}
}

void setup() {
    hardware_begin();
    live_begin();
    console.page = Page::Overview;
    Serial.printf("live:setup_done\n");
}

void loop() {
    const uint32_t now = millis();
    if (button_down()) {
        if (!button_held) { button_held = true; button_started = now; }
    } else if (button_held) {
        const uint32_t held_ms = now - button_started;
        button_held = false;
        if (held_ms >= 1000) select_button(4);
        else if (held_ms >= 30) select_button(console.page == Page::Overview ? 1 : console.page == Page::Diagnostics ? 2 : 0);
    }
    if (static_cast<uint32_t>(now - last_poll) >= 300 &&
        static_cast<uint32_t>(now - last_render) >= 350) {
        last_poll = now;
        Point point{-1, -1};
        if (read_touch(point)) apply(console.tap(point));
    }
    const bool automatic_due = automatic_updates(console.page) && now - last_live_render >= (console.page == Page::Overview ? 1000u : 5000u) && now - last_render >= 750;
    if ((dirty || automatic_due) && screen_buffer()) {
        memset(screen_buffer(), 0xFF, kWidth * kHeight / 2);
        EpaperCanvas canvas;
        if(last_live_render==0) Serial.printf("live:first_snapshot\n");
        uint32_t render_time = 0, a1_last_seen = 0;
        Health a1_health = Health::Unknown;
        render_latest_snapshot(live_snapshot, [] { return millis(); },
            [&](const LiveSnapshot& live, uint32_t sampled_after_capture) {
                render_time = sampled_after_capture;
                a1_last_seen = live.nodes[0].last_seen_ms;
                a1_health = health_at(live.nodes[0], render_time);
                if(last_live_render==0) Serial.printf("live:first_draw\n");
                draw_console(canvas, console, diagnostics(), live.nodes, render_time, live.deployment, live.image, live.mission_status, live.mission.run, live.mission_requested);
            });
        last_live_render = now;
        const uint64_t candidate = framebuffer_fingerprint(screen_buffer(), kWidth * kHeight / 2);
        const bool should_refresh = refresh_policy.needs_refresh(candidate, dirty, sleep_requested);
        Serial.printf("ui:render page=%u manual=%u sleep=%u first=%u changed=%u refresh=%u loop_ms=%u sample_ms=%u a1_seen=%u a1_health=%s previous=%016llx candidate=%016llx\n",
            unsigned(console.page), unsigned(dirty), unsigned(sleep_requested), unsigned(!refresh_policy.has_frame),
            unsigned(candidate != refresh_policy.displayed), unsigned(should_refresh), unsigned(now), unsigned(render_time),
            unsigned(a1_last_seen), health_name(a1_health), (unsigned long long)refresh_policy.displayed, (unsigned long long)candidate);
        if (should_refresh) {
            if(last_render==0) Serial.printf("live:first_refresh\n");
            const bool full = require_full_refresh(refresh_policy.has_frame, displayed_page,
                                                  console.page, full_requested, sleep_requested);
            if (refresh_screen(full)) {
                refresh_policy.did_refresh(candidate);
                displayed_page = console.page;
            }
            if(last_render==0) Serial.printf("live:first_refresh_done\n");
            last_render = millis();
        }
        dirty = false;
        full_requested = false;
        if (sleep_requested) {
            sleep_requested = false;
            if (!live_pause(true)) { console.page = Page::Detail; dirty = true; }
            else if (!enter_sleep()) { live_pause(false); console.page = Page::Diagnostics; dirty = true; }
        }
    }
    delay(10);
}
