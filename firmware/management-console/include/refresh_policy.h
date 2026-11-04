#pragma once
#include <cstddef>
#include <cstdint>

namespace flockinator {
// A concurrent radio update can make last_seen newer than the loop's old clock.
// Read the clock only after capturing observations, before interpreting freshness.
template <typename Capture, typename Clock, typename Render>
void render_latest_snapshot(Capture capture, Clock clock, Render render) {
    const auto snapshot = capture();
    render(snapshot, clock());
}

// A compact comparison of the actual rendered pixels, not just telemetry fields.
// This is a display-change heuristic, not a security or integrity checksum.
inline uint64_t framebuffer_fingerprint(const uint8_t* pixels, size_t size) {
    uint64_t value = 14695981039346656037ULL;
    for (size_t i = 0; i < size; ++i) {
        value ^= pixels[i];
        value *= 1099511628211ULL;
    }
    return value;
}

struct RefreshPolicy {
    bool has_frame = false;
    uint64_t displayed = 0;

    bool needs_refresh(uint64_t candidate, bool manual, bool sleeping) const {
        return !has_frame || manual || sleeping || candidate != displayed;
    }

    void did_refresh(uint64_t fingerprint) {
        displayed = fingerprint;
        has_frame = true;
    }
};
}
