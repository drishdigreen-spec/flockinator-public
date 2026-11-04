#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void standalone_init(void);
void standalone_web(void* server);
bool standalone_usb(const char* line);
unsigned standalone_pin(void);
bool standalone_ready(void);
void standalone_network(bool connected);
bool standalone_touch(bool start,unsigned scenario,unsigned goal,unsigned seconds,bool repeat);
typedef struct {bool known,live,running;unsigned age_ms,uptime,ram,state;char version[17];float x,y;} panel_view_t;
void standalone_panel(int i,panel_view_t* view);
#ifdef __cplusplus
}
#endif
