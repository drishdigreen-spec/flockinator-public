// Use the panels' own scripted timeline and camera coordinates on the host.
#include "../../firmware/node-platform/include/mission_world.h"
extern "C" int mission_node(int scenario, int goal, int seconds, bool repeat,
                            int64_t elapsed, int index, float *pose) {
  recon::Runtime runtime;
  runtime.apply({1, 271828, uint16_t(seconds), uint8_t(scenario), uint8_t(goal), repeat},
                true, 0, 0);
  if (elapsed < 0 || elapsed >= 86400000 || !runtime.active(uint32_t(elapsed)))
    return recon::READY;
  const auto scene = runtime.frame(uint32_t(elapsed), index);
  const auto cycle_ms = (32 + seconds + 31) * 1000;
  auto p = mission_world::pose(index, (elapsed % cycle_ms) / 1000.f, scene);
  pose[0] = p.position.x; pose[1] = p.position.y; pose[2] = p.position.z;
  pose[3] = p.heading;
  return scene.state;
}
