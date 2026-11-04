#include "world_render.h"
#include <unity.h>
using namespace world;
void setUp(){} void tearDown(){}
void geometry(){
 Pose p{{0,0,20},0,0,0};auto q=project(p,{10,100,0});
 TEST_ASSERT_FLOAT_WITHIN(.001f,35.7f,q.x);TEST_ASSERT_FLOAT_WITHIN(.001f,36.9f,q.y);
 TEST_ASSERT_TRUE(project(p,{0,-100,20}).behind);
 p.heading=90;q=project(p,{100,0,20});TEST_ASSERT_FLOAT_WITHIN(.001f,31.5f,q.x);
}
void runtime(){
 Runtime r;r.start(100);auto a=r.sample(1100,0);auto b=r.sample(1350,0);
 TEST_ASSERT_TRUE(a.pose.position.y<b.pose.position.y);
 r.pause(1350);auto paused=r.sample(9000,0);TEST_ASSERT_FLOAT_WITHIN(.001f,b.pose.position.y,paused.pose.position.y);
 r.play(9000);r.interrupt(9000);TEST_ASSERT_EQUAL(Stale,r.sample(11000,0).freshness);
 auto frozen=r.sample(11000,0);r.resume(11000,0);auto resumed=r.sample(11000,0);
 TEST_ASSERT_EQUAL(Resync,resumed.freshness);TEST_ASSERT_FLOAT_WITHIN(.001f,frozen.pose.position.y,resumed.pose.position.y);
 TEST_ASSERT_EQUAL(Live,r.sample(11750,0).freshness);
 auto before=r.sample(12000,0);TEST_ASSERT_TRUE(r.impact(12000,0));auto impact=r.sample(12000,0);
 TEST_ASSERT_FLOAT_WITHIN(.001f,before.pose.position.z,impact.pose.position.z);
 TEST_ASSERT_EQUAL(Ground,r.sample(14000,0).stage);TEST_ASSERT_EQUAL(Static,r.sample(15000,0).stage);TEST_ASSERT_EQUAL(Ground,r.sample(20000,0).stage);
}
void frames(){
 static node::Frame a,b;
 for(int node=0;node<16;node++)for(int sensor=0;sensor<5;sensor++){
  Runtime r;r.start(0);auto s=r.sample(30000,node);render(a,s,node,Sensor(sensor));render(b,s,node,Sensor(sensor));
  TEST_ASSERT_FALSE(a.clipped);TEST_ASSERT_EQUAL_MEMORY(a.pixels,b.pixels,sizeof(a.pixels));
  r.impact(30000,node);s=r.sample(32000,node);render(a,s,node,Sensor(sensor));TEST_ASSERT_FALSE(a.clipped);
 }
}
int main(){UNITY_BEGIN();RUN_TEST(geometry);RUN_TEST(runtime);RUN_TEST(frames);return UNITY_END();}
