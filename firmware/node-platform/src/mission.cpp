#include "mission.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include <cmath>
namespace {
portMUX_TYPE guard = portMUX_INITIALIZER_UNLOCKED;
recon::Runtime runtime;
int panel_index = 0;
uint32_t now() { return esp_timer_get_time() / 1000; }
} // namespace
void mission_init(const char *label) {
  if (label && label[0] >= 'A' && label[0] <= 'D' && label[1] >= '1' &&
      label[1] <= '4')
    panel_index = (label[1] - '1') * 4 + label[0] - 'A';
}
recon::Runtime mission_snapshot() {
  portENTER_CRITICAL(&guard);
  auto r = runtime;
  portEXIT_CRITICAL(&guard);
  return r;
}
bool mission_apply(const recon::Config &c, bool start, uint32_t delay) {
  auto t = now();
  portENTER_CRITICAL(&guard);
  bool ok = runtime.apply(c, start, delay, t);
  portEXIT_CRITICAL(&guard);
  return ok;
}
const char *mission_command(cJSON *j) {
  auto *op = cJSON_GetObjectItemCaseSensitive(j, "op");
  if (!cJSON_IsString(op))
    return "invalid_operation";
  bool start = !strcmp(op->valuestring, "mission_start");
  if (!start && strcmp(op->valuestring, "mission_stop"))
    return "unknown_mission_operation";
  for (auto *v = j->child; v; v = v->next) {
    if (!v->string)
      return "invalid_field";
    for (auto *p = j->child; p != v; p = p->next)
      if (!strcmp(p->string, v->string))
        return "duplicate_field";
    bool allowed = false;
    for (auto k : {"op", "v", "id", "target", "run", "seed", "seconds",
                   "scenario", "goal", "repeat", "delay_ms"})
      if (!strcmp(k, v->string))
        allowed = true;
    if (!allowed)
      return "unknown_mission_field";
  }
  auto integer = [&](const char *k, uint32_t max, uint32_t fallback,
                     uint32_t &out) {
    auto *v = cJSON_GetObjectItemCaseSensitive(j, k);
    if (!v) {
      out = fallback;
      return true;
    }
    if (!cJSON_IsNumber(v) || v->valuedouble < 0 || v->valuedouble > max ||
        std::floor(v->valuedouble) != v->valuedouble)
      return false;
    out = uint32_t(v->valuedouble);
    return true;
  };
  auto c = mission_snapshot().config;
  uint32_t run, seed, seconds, scenario, goal, delay;
  auto *repeat = cJSON_GetObjectItemCaseSensitive(j, "repeat");
  if (!integer("run", UINT32_MAX, 0, run) ||
      !integer("seed", UINT32_MAX, start ? 1 : c.seed, seed) ||
      !integer("seconds", 96, start ? 64 : c.seconds, seconds) ||
      !integer("scenario", 2, start ? 0 : c.scenario, scenario) ||
      !integer("goal", 2, start ? 0 : c.goal, goal) ||
      !integer("delay_ms", 60000, 0, delay) ||
      (repeat && !cJSON_IsBool(repeat)))
    return "invalid_mission_fields";
  c = {run,
       seed,
       uint16_t(seconds),
       uint8_t(scenario),
       uint8_t(goal),
       repeat  ? bool(cJSON_IsTrue(repeat))
       : start ? true
               : c.repeat};
  return mission_apply(c, start, delay) ? nullptr : "mission_rejected";
}
void mission_json(cJSON *root) {
  auto r = mission_snapshot();
  auto t = now();
  auto s = r.frame(t, panel_index);
  auto *j = cJSON_AddObjectToObject(root, "mission");
  cJSON_AddNumberToObject(j, "version", 1);
  cJSON_AddStringToObject(j, "overview", recon::overview_name(r.summary(t, panel_index)));
  cJSON_AddStringToObject(j, "source", "scripted_simulation");
  cJSON_AddNumberToObject(j, "run", r.config.run);
  cJSON_AddBoolToObject(j, "running", r.active(t));
  cJSON_AddBoolToObject(j, "waiting", r.waiting(t));
  cJSON_AddStringToObject(j, "state", recon::name(s.state));
  cJSON_AddNumberToObject(j, "elapsed_ms", r.elapsed(t));
  cJSON_AddNumberToObject(j, "cycle", s.cycle);
  cJSON_AddNumberToObject(j, "scenario", r.config.scenario);
  cJSON_AddNumberToObject(j, "goal", r.config.goal);
  cJSON_AddNumberToObject(j, "seconds", r.config.seconds);
  cJSON_AddBoolToObject(j, "repeat", r.config.repeat);
  cJSON_AddStringToObject(j, "sensor", recon::sensor_name(s.sensor));
  cJSON_AddNumberToObject(j, "variant", s.variation);
}
void mission_health(uint8_t *b) {
  auto r = mission_snapshot();
  auto t = now();
  auto s = r.frame(t, panel_index);
  b[96] = 1;
  b[97] = (r.active(t) ? 1 : 0) | (r.waiting(t) ? 2 : 0);
  b[98] = s.state;
  b[99] = s.sensor;
  recon::put32(b + 100, r.config.run);
  recon::put32(b + 104, r.elapsed(t));
  recon::put32(b + 108, s.cycle);
  b[112] = r.config.scenario;
  b[113] = r.config.goal;
  b[114] = s.variation;
  b[115] = r.config.repeat;
  b[116] = 1;
  b[117] = uint8_t(r.summary(t, panel_index));
}
