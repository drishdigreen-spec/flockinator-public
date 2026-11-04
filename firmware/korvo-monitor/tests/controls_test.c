#include <assert.h>
#include "../main/controls.h"
int main(void) {
    controls_t c = {.volume=20};
    for(int i=0;i<30;i++) controls_apply(&c, CONTROL_UP);
    assert(c.volume==100);
    for(int i=0;i<30;i++) controls_apply(&c, CONTROL_DOWN);
    assert(c.volume==0);
    controls_apply(&c, CONTROL_MUTE); assert(c.muted);
    controls_apply(&c, CONTROL_UP); assert(!c.muted && c.volume==5);
    controls_apply(&c, CONTROL_SETTINGS); assert(c.settings);
    controls_apply(&c, CONTROL_SLEEP); assert(c.sleeping);
    controls_apply(&c, CONTROL_HOME); assert(!c.sleeping && !c.settings);
    controls_apply(&c, CONTROL_SLEEP); controls_apply(&c, CONTROL_WAKE); assert(!c.sleeping);
}
