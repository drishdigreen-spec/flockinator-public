#include "survey_render.h"
#include <unity.h>
void setUp(){} void tearDown(){}
survey::Packet packet(){survey::Packet p{};p.run=10;p.seq=1;p.node=0;p.pose={{0,0,24},359,-5,0};p.energy=10000;p.distance=100;p.state=2;return p;}
void accepts_only_valid_new_samples(){
 survey::Runtime r;auto p=packet();TEST_ASSERT_TRUE(r.receive(p,0,100));TEST_ASSERT_FALSE(r.receive(p,0,200));p.seq++;p.energy=10001;TEST_ASSERT_FALSE(r.receive(p,0,200));p.energy=9000;TEST_ASSERT_FALSE(r.receive(p,1,200));p.run=9;TEST_ASSERT_FALSE(r.receive(p,0,200));p.run=10;TEST_ASSERT_TRUE(r.receive(p,0,200));
}
void wraps_interpolates_and_freezes(){
 survey::Runtime r;auto p=packet();r.receive(p,0,100);p.seq++;p.pose.heading=1;p.pose.position.y=10;r.receive(p,0,600);
 auto mid=r.sample(850);TEST_ASSERT_FLOAT_WITHIN(.01,5,mid.pose.position.y);TEST_ASSERT_FLOAT_WITHIN(.01,0,mid.pose.heading);
 TEST_ASSERT_EQUAL(world::Stale,r.sample(2600).freshness);TEST_ASSERT_FLOAT_WITHIN(.01,10,r.sample(10000).pose.position.y);
 p.seq++;p.pose.position.y=100;r.receive(p,0,10000);TEST_ASSERT_FLOAT_WITHIN(.01,10,r.sample(10000).pose.position.y);
}
void frames_are_bounded(){static node::Frame f;survey::Runtime r;auto p=packet();for(int state=0;state<8;state++){p.seq++;p.state=state;r.receive(p,0,p.seq*100);for(int sensor=0;sensor<5;sensor++){survey::render(f,r,p.seq*100,world::Sensor(sensor));TEST_ASSERT_FALSE(f.clipped);}}}
int main(){UNITY_BEGIN();RUN_TEST(accepts_only_valid_new_samples);RUN_TEST(wraps_interpolates_and_freezes);RUN_TEST(frames_are_bounded);return UNITY_END();}
