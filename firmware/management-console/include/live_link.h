#pragma once
#include "console_model.h"
namespace flockinator {
struct LiveSnapshot {
    std::array<Node,16> nodes{};
    bool radio=false, wifi=false, busy=false;
    char ip[20]{}, image[65]{}, deployment[80]{"Idle"};
    uint32_t offset=0,total=0;
    recon::Config mission;bool mission_requested=false;
    uint16_t mission_accepted=0,mission_failed=0;
    char mission_status[80]{"Ready / select scenario, then Launch"};
};
void live_begin();
LiveSnapshot live_snapshot();
bool live_deploy_selected(int index);
bool live_mission(const recon::Config& config,bool start);
bool live_can_sleep();
bool live_pause(bool paused);
}
