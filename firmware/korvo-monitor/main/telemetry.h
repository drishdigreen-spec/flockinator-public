#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    unsigned index, state;
    char version[17];
    uint32_t uptime, ram;
} telemetry_t;

/* USB line: F1 index state version uptime_seconds free_internal_KiB.
 * State 0: no response, 1: identity-checked status, 2: validation/credential error.
 * Reject complete malformed frames atomically; they must not refresh freshness. */
static inline bool telemetry_parse(const char *line, telemetry_t *out)
{
    telemetry_t t = {0};
    char index[3], state[2], uptime[11], ram[11], extra;
    if (sscanf(line, "F1 %2[0-9] %1[0-9] %16[A-Za-z0-9._-] %10[0-9] %10[0-9] %c",
               index, state, t.version, uptime, ram, &extra) != 5) return false;
    t.index = (unsigned)strtoul(index, NULL, 10);
    t.state = (unsigned)strtoul(state, NULL, 10);
    unsigned long long u = strtoull(uptime, NULL, 10), r = strtoull(ram, NULL, 10);
    if (t.index >= 16 || t.state > 2 || u > UINT32_MAX || r > UINT32_MAX) return false;
    t.uptime = (uint32_t)u; t.ram = (uint32_t)r;
    *out = t;
    return true;
}
static inline unsigned telemetry_state(unsigned state, uint64_t received, uint64_t now)
{
    return now - received > 20000 ? 3 : state;
}
