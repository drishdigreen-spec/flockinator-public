#include <unity.h>
#include "avatar_render.h"
void setUp(){}void tearDown(){}
void render_is_bounded(){
 node::Frame f;node::AvatarState s;uint8_t pixels[8192]{};
 for(unsigned a=0;a<6;a++){s.set(node::Activity(a),node::Attention::Calm,node::Mood::Neutral,-1,60,0);node::avatar_render(f,pixels,"D4",s,100,123,false,true,true,true);TEST_ASSERT_FALSE(f.clipped);}
 f.clear(0xffff);node::avatar_render(f,pixels,"A1",s,100,123,true,false,false,false);TEST_ASSERT_EQUAL(0,f.pixels[32*64+32]);TEST_ASSERT_FALSE(f.clipped);
}
int main(){UNITY_BEGIN();RUN_TEST(render_is_bounded);return UNITY_END();}
