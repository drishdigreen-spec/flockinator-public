#pragma once
#include "console_model.h"

namespace flockinator {
struct TouchGesture {
    bool held = false;
    bool accept(bool fresh, bool contact, Point point) {
        if (!fresh) return false; // Missing/failed reads do not imply release.
        if (!contact) { held = false; return false; }
        const bool first = !held;
        held = true;
        return first && point.valid();
    }
};
inline bool automatic_updates(Page page) {
    return page == Page::Overview || page == Page::Detail || page == Page::Missions;
}
}
