#include <assert.h>
#include "../main/telemetry.h"
int main(void) {
    telemetry_t t;
    assert(telemetry_parse("F1 0 1 0.10.1 123 254", &t));
    assert(t.index == 0 && t.state == 1 && t.uptime == 123);
    assert(!telemetry_parse("F1 16 1 0.10.1 123 254", &t));
    assert(!telemetry_parse("F1 0 3 v1 0 0", &t));
    assert(!telemetry_parse("F1 0 1 v1 -1 0", &t));
    assert(!telemetry_parse("F1 0 1 v1 4294967296 0", &t));
    assert(!telemetry_parse("F1 0 1 v1 1 2 junk", &t));
    assert(!telemetry_parse("F2 0 1 v1 1 2", &t));
    assert(!telemetry_parse("F1 0 1 v1", &t));
    assert(telemetry_parse("F1 15 0 - 0 0", &t));
    assert(telemetry_state(0, 100, 100) == 0);
    assert(telemetry_state(1, 100, 20100) == 1);
    assert(telemetry_state(1, 100, 20101) == 3);
    assert(telemetry_state(2, 100, 20101) == 3);
}
