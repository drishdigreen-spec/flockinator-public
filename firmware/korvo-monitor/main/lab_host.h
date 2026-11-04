#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct {
    unsigned seed,turn,link;
    int clear,altered,solo;
    bool paused;
    char ip[16];
    uint8_t correct[16]; /* 0 waiting, 1 both correct, 2 only clear, 3 only altered, 4 neither */
} lab_metrics_t;
void lab_start(void);
void lab_metrics(lab_metrics_t* out);
bool lab_provision(const char* line);
#ifdef __cplusplus
}
#endif
