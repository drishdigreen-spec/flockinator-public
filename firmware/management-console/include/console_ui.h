#pragma once
#include <cstdio>
#include "hardware.h"

namespace flockinator {

template <typename Canvas>
void draw_console(Canvas& canvas, const Console& model, const Diagnostics& diag,
                  const std::array<Node, 16>& nodes, uint32_t now = 0, const char* deployment = "Idle", const char* image = "", const char* mission_status = "Ready", uint32_t mission_run = 0, bool requested = false) {
    canvas.text(24, 48, "FLOCKINATOR", 32);
    canvas.text(560, 44, "LIVE / authenticated nodes", 18);
    canvas.rect({24, 62, 912, 2}, true);
    char line[112];
    if (model.page == Page::Overview) {
        canvas.text(24, 94, "Mission status / OM = on mission", 18);
        for (int i = 0; i < 16; ++i) {
            const Rect card = card_rect(i);
            canvas.rect(card, false);
            const Health health = overview_health(nodes[i], now);
            // Solid, hollow and striped markers supplement the textual state.
            const uint8_t shade = health == Health::Healthy ? 0x00 : 0x80;
            canvas.rect({card.x + 12, card.y + 14, 12, 12}, health != Health::Unknown, shade);
            if (health == Health::Stale || health == Health::Offline) {
                canvas.rect({card.x + 12, card.y + 18, 12, 3}, true, 0xFF);
            }
            std::snprintf(line, sizeof(line), "%c%c  %s", 'A'+i/4, '1'+i%4,
                health == Health::Healthy ? "" : health_name(health));
            canvas.text(card.x + 35, card.y + 28, line, 18);
            canvas.text(card.x + 12, card.y + 57, overview_label(nodes[i], now), 18);
        }
        canvas.text(24, 448, "Simulation status / tap a node for hardware details", 12);
    } else if (model.page == Page::Detail) {
        const Node& node = nodes[model.selected];
        std::snprintf(line, sizeof(line), "NODE %c%c / %s", 'A'+model.selected/4, '1'+model.selected%4, health_name(health_at(node,now)));
        canvas.text(24, 111, line, 32);
        std::snprintf(line,sizeof(line),"%s / %s",node.registered ? node.mac : "Not registered",node.observed ? node.version : "Awaiting authenticated health");
        canvas.text(24,160,line,18);
        std::snprintf(line,sizeof(line),"Receiver %u / OTA state %u / last seen %lu s",node.receiver,node.ota_state,(unsigned long)(node.observed ? (now-node.last_seen_ms)/1000 : 0));
        canvas.text(24,205,line,18);
        if(node.mission_capable){std::snprintf(line,sizeof(line),"SIM %s / run %lu / %lu s / cycle %lu",recon::name(node.mission_state),(unsigned long)node.mission_run,(unsigned long)(node.mission_elapsed/1000),(unsigned long)node.mission_cycle);canvas.text(24,249,line,18);}
        else canvas.text(24,249,node.deployment_verified ? "Deployment verified: expected image booted valid" : "Deployment verification pending",18);
        std::snprintf(line,sizeof(line),"Stored image: %.60s",image[0] ? image : "None / upload via USB");
        canvas.text(24,291,line,18);
        canvas.text(24,336,deployment,18);
        canvas.rect({24,375,640,62},false);
        canvas.text(40,415,"Deploy stored image to this node",18);
    } else if(model.page==Page::Missions){
        canvas.text(24,103,"MISSION CONTROL / scripted simulation",32);
        const Rect fields[]={{24,120,560,60},{24,190,560,60},{24,260,270,60},{310,260,274,60},{24,370,270,55},{310,370,274,55}};
        for(auto r:fields)canvas.rect(r,false);
        std::snprintf(line,sizeof(line),"Scenario: %s",recon::scenario_name(model.draft.scenario));canvas.text(38,159,line,18);
        std::snprintf(line,sizeof(line),"Goal: %s",recon::goal_name(model.draft.goal));canvas.text(38,229,line,18);
        std::snprintf(line,sizeof(line),"Survey: %u s",model.draft.seconds);canvas.text(38,299,line,18);
        canvas.text(324,299,model.draft.repeat?"Repeat: ON":"Repeat: OFF",18);
        canvas.text(38,405,"Launch",18);canvas.text(324,405,"Stop all",18);
        unsigned fresh=0,confirmed=0,running=0,waiting=0;
        for(const auto& n:nodes){auto h=health_at(n,now);bool live=n.observed&&h!=Health::Stale&&h!=Health::Offline;
            if(live&&n.mission_capable)++fresh;
            if(live&&n.mission_capable&&(!requested?!n.mission_running:n.mission_run==mission_run&&n.mission_running&&!n.mission_waiting))++confirmed;
            if(live&&n.mission_running)++running;
            if(live&&n.mission_waiting)++waiting;
        }
        std::snprintf(line,sizeof(line),"Ready link: %u / 16",fresh);canvas.text(610,154,line,18);
        std::snprintf(line,sizeof(line),"Confirmed: %u / 16",mission_run?confirmed:0);canvas.text(610,199,line,18);
        std::snprintf(line,sizeof(line),"Running: %u",running);canvas.text(610,244,line,18);
        std::snprintf(line,sizeof(line),"Scheduled: %u",waiting);canvas.text(610,289,line,18);
        canvas.text(24,356,"Tap settings to cycle; changes apply on next launch.",18);
        canvas.text(24,453,mission_status,12);
    } else if (model.page == Page::Diagnostics) {
        canvas.text(24, 103, "Handheld diagnostics", 32);
        std::snprintf(line, sizeof(line), "Build %s / display buffer %s", kVersion, diag.display_buffer ? "ready" : "unavailable");
        canvas.text(24, 140, line, 18);
        std::snprintf(line, sizeof(line), "Touch %s / battery voltage unverified", diag.touch ? "detected" : "unavailable");
        canvas.text(24, 174, line, 18);
        if (diag.sd) {
            std::snprintf(line, sizeof(line), "SD mounted / %s / %lu MiB physical capacity", diag.sd_type, static_cast<unsigned long>(diag.sd_capacity_mb));
        } else {
            std::snprintf(line, sizeof(line), "SD mount failed / card, format or connection unverified");
        }
        canvas.text(24, 208, line, 18);
        canvas.text(24, 242, "Images stored under /flockinator/images", 18);
        std::snprintf(line, sizeof(line), "Free internal heap %lu KiB / PSRAM %lu KiB",
            static_cast<unsigned long>(diag.internal_free / 1024), static_cast<unsigned long>(diag.psram_free / 1024));
        canvas.text(24, 276, line, 18);
        std::snprintf(line, sizeof(line), "Previous refresh %lu ms / completed refreshes %lu",
            static_cast<unsigned long>(diag.refresh_ms), static_cast<unsigned long>(diag.redraws));
        canvas.text(24, 310, line, 18);
        canvas.text(24, 344, diag.note, 18);
        canvas.text(24, 380, "Snapshot / tap Refresh", 12);
        canvas.rect({640,365,296,72},false);canvas.text(655,410,"Touch alignment",18);
        canvas.text(24, 414, "Button: change page / hold 1 second then release to sleep", 12);
    } else if (model.page == Page::Alignment) {
        canvas.text(150, 109, "Tap the five targets to check alignment", 18);
        const Point targets[] = {{32, 130}, {928, 130}, {480, 270}, {32, 426}, {928, 426}};
        for (Point point : targets) {
            canvas.rect({point.x - 15, point.y - 15, 31, 31}, false);
            canvas.rect({point.x - 10, point.y, 21, 1}, true);
            canvas.rect({point.x, point.y - 10, 1, 21}, true);
        }
        if (model.last_touch.valid()) {
            std::snprintf(line, sizeof(line), "Last touch: x=%d  y=%d", model.last_touch.x, model.last_touch.y);
        } else {
            std::snprintf(line, sizeof(line), "No mapped touch yet");
        }
        canvas.text(230, 345, line, 18);
        canvas.text(150, 390, "Orientation is provisional until checked on your board", 12);
    } else {
        canvas.text(24, 171, "SLEEPING - status frozen", 32);
        canvas.text(24, 234, "Press the physical button to wake.", 18);
        canvas.text(24, 280, "This retained image is not live telemetry.", 18);
        canvas.text(24, 326, "The swarm runs independently of this remote.", 18);
        return;
    }
    const char* labels[] = {"Overview", "Diagnostics", "Missions", "Refresh", "Sleep"};
    for (int i = 0; i < 5; ++i) {
        const Rect button = button_rect(i);
        canvas.rect(button, false);
        canvas.text(button.x + 14, button.y + 36, labels[i], 18);
    }
}
} // namespace flockinator
