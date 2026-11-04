#pragma once
#include <stdbool.h>
typedef enum {CONTROL_UP, CONTROL_DOWN, CONTROL_SLEEP, CONTROL_HOME,
              CONTROL_SETTINGS, CONTROL_MUTE, CONTROL_WAKE, CONTROL_TEST} control_action_t;
typedef struct {int volume; bool muted, sleeping, settings;} controls_t;
static inline void controls_apply(controls_t *c, control_action_t action)
{
    switch(action) {
        case CONTROL_UP: c->volume = c->volume >= 95 ? 100 : c->volume+5; c->muted=false; break;
        case CONTROL_DOWN: c->volume = c->volume <= 5 ? 0 : c->volume-5; c->muted=false; break;
        case CONTROL_MUTE: c->muted=!c->muted; break;
        case CONTROL_SLEEP: c->sleeping=!c->sleeping; break;
        case CONTROL_HOME: c->sleeping=false; c->settings=false; break;
        case CONTROL_SETTINGS: c->settings=true; break;
        case CONTROL_WAKE: c->sleeping=false; break;
        case CONTROL_TEST: break;
    }
}
