#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
#include "../../shared/recon/model.h"

namespace flockinator {

constexpr size_t kSerialTxBytes = 32768;
constexpr size_t kSerialReplyMax = 16384;
constexpr int kWidth = 960;
constexpr int kHeight = 540;
constexpr uint32_t kStaleMs = 30000;
constexpr uint32_t kOverviewStaleMs = 6000;
constexpr uint32_t kHealthPollMs = 2000;
constexpr const char* kVersion = "0.3.3-missions";

struct Point {
    int x;
    int y;
    bool valid() const { return x >= 0 && y >= 0 && x < kWidth && y < kHeight; }
};

struct Rect {
    int x, y, w, h;
    bool contains(Point p) const {
        return p.valid() && p.x >= x && p.y >= y && p.x < x + w && p.y < y + h;
    }
};

inline Rect card_rect(int index) {
    if (index < 0 || index >= 16) return {0, 0, 0, 0};
    return {24 + index / 4 * 230, 110 + index % 4 * 80, 218, 70};
}

inline Rect button_rect(int index) {
    if (index < 0 || index >= 5) return {0, 0, 0, 0};
    return {24 + index * 184, 462, 176, 56};
}

inline int node_at(Point p) {
    for (int i = 0; i < 16; ++i) if (card_rect(i).contains(p)) return i;
    return -1;
}

// Keep SensorLib transforms off: its mirrored maximum is not a last-pixel index.
inline Point landscape_touch(int raw_x, int raw_y) {
    if (raw_x < 0 || raw_x >= 540 || raw_y < 0 || raw_y >= 960) return {-1, -1};
    return {raw_y, 539 - raw_x};
}

enum class Health { Unknown, Healthy, Stale, Offline, Warning };
struct Node {
    uint8_t id; Health health; bool observed; uint32_t last_seen_ms;
    bool registered=false; char mac[18]{}; char version[17]{}; char image[65]{};
    uint8_t receiver=0, ota_state=0; bool deployment_verified=false;
    bool mission_capable=false,mission_running=false,mission_waiting=false;
    uint8_t mission_state=recon::READY,mission_sensor=recon::NV,mission_scenario=0,mission_goal=0;
    recon::Overview mission_overview=recon::Overview::Unknown;
    uint32_t mission_run=0,mission_elapsed=0,mission_cycle=0;
    uint32_t boots=0; bool sd=false; uint8_t sensors=0, audio=0;
};

inline Health health_at(const Node& node, uint32_t now) {
    if (!node.observed) return Health::Unknown;
    if (static_cast<uint32_t>(now - node.last_seen_ms) >= 90000) return Health::Offline;
    if (node.health == Health::Offline) return Health::Offline;
    if (static_cast<uint32_t>(now - node.last_seen_ms) >= kStaleMs) return Health::Stale;
    return node.health;
}

inline Health overview_health(const Node& node, uint32_t now) {
    auto health = health_at(node, now);
    if (node.observed && health != Health::Offline && now-node.last_seen_ms >= kOverviewStaleMs)
        return Health::Stale;
    return health;
}
inline const char* overview_label(const Node& node, uint32_t now) {
    auto health = overview_health(node, now);
    return node.observed && node.mission_capable && health != Health::Stale && health != Health::Offline
        ? recon::overview_name(node.mission_overview) : "--";
}
inline const char* health_name(Health health) {
    switch (health) {
        case Health::Healthy: return "Healthy";
        case Health::Stale: return "Stale";
        case Health::Offline: return "Offline";
        case Health::Warning: return "Warning";
        default: return "Unknown";
    }
}

// Fixed fixture time: idle demo nodes do not silently age into real-looking failures.
constexpr uint32_t kDemoNow = 120000;
inline std::array<Node, 16> demo_nodes() {
    std::array<Node, 16> nodes{};
    for (int i = 0; i < 16; ++i) nodes[i] = {static_cast<uint8_t>(i + 1), Health::Healthy, true, kDemoNow - 2000};
    nodes[5].health = Health::Warning;
    nodes[6] = {7, Health::Healthy, true, kDemoNow - 45000};
    nodes[10] = {11, Health::Offline, true, kDemoNow - 90000};
    nodes[15].observed = false;
    return nodes;
}

enum class Page { Overview, Detail, Diagnostics, Alignment, Missions, Sleeping };
enum class Action { None, Redraw, Sleep, Deploy, Refresh, MissionStart, MissionStop };

struct Console {
    Page page = Page::Diagnostics;
    int selected = 0;
    recon::Config draft;
    Point last_touch{-1, -1};
    constexpr bool can_send_node_commands() const { return page == Page::Detail; }

    Action tap(Point point) {
        if (!point.valid() || page == Page::Sleeping) return Action::None;
        for (int i = 0; i < 5; ++i) {
            if (!button_rect(i).contains(point)) continue;
            if (i == 0) page = Page::Overview;
            if (i == 1) page = Page::Diagnostics;
            if (i == 2) page = Page::Missions;
            if (i == 3) return Action::Refresh;
            if (i == 4) { page = Page::Sleeping; return Action::Sleep; }
            return Action::Redraw;
        }
        if(page==Page::Diagnostics && Rect{640,365,296,72}.contains(point)){page=Page::Alignment;return Action::Redraw;}
        if(page==Page::Missions){
            if(Rect{24,120,560,60}.contains(point)){draft.scenario=(draft.scenario+1)%3;return Action::Redraw;}
            if(Rect{24,190,560,60}.contains(point)){draft.goal=(draft.goal+1)%3;return Action::Redraw;}
            if(Rect{24,260,270,60}.contains(point)){draft.seconds=draft.seconds==64?96:64;return Action::Redraw;}
            if(Rect{310,260,274,60}.contains(point)){draft.repeat=!draft.repeat;return Action::Redraw;}
            if(Rect{24,370,270,55}.contains(point))return Action::MissionStart;
            if(Rect{310,370,274,55}.contains(point))return Action::MissionStop;
        }
        if (page == Page::Detail && Rect{24, 375, 640, 62}.contains(point)) return Action::Deploy;
        if (page == Page::Overview) {
            const int node = node_at(point);
            if (node >= 0) { selected = node; page = Page::Detail; return Action::Redraw; }
        } else if (page == Page::Alignment) {
            last_touch = point;
            return Action::Redraw;
        }
        return Action::None;
    }
};

} // namespace flockinator
