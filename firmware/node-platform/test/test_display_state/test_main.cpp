#include <unity.h>
#include "display_state.h"
void setUp() {} void tearDown() {}
void expires_across_wrap() {
    node::AvatarState s;
    TEST_ASSERT_TRUE(s.set(node::Activity::Listening,node::Attention::Attentive,node::Mood::Curious,-1,2,0xfffffff0));
    TEST_ASSERT_TRUE(s.active(100));
    TEST_ASSERT_FALSE(s.active(3000));
}
void sleeping_validation_atomic() {
    node::AvatarState s;
    TEST_ASSERT_TRUE(s.set(node::Activity::Processing,node::Attention::Calm,node::Mood::Content,-1,60,100));
    TEST_ASSERT_FALSE(s.set(node::Activity::Sleeping,node::Attention::Urgent,node::Mood::Neutral,-1,60,110));
    TEST_ASSERT_EQUAL_INT(int(node::Activity::Processing),int(s.activity));
    TEST_ASSERT_FALSE(s.set(node::Activity::Sleeping,node::Attention::Calm,node::Mood::Frightened,-1,60,110));
}
void bounded_requests() {
    node::AvatarState s;
    TEST_ASSERT_FALSE(s.set(node::Activity::Idle,node::Attention::Calm,node::Mood::Neutral,-1,0,0));
    TEST_ASSERT_FALSE(s.set(node::Activity::Idle,node::Attention::Calm,node::Mood::Neutral,5,60,0));
    TEST_ASSERT_FALSE(s.set(node::Activity(99),node::Attention::Calm,node::Mood::Neutral,-1,60,0));
}
void expression_semantics() {
    node::AvatarState s;s.set(node::Activity::Idle,node::Attention::Calm,node::Mood::Content,-1,60,0);TEST_ASSERT_EQUAL(34,node::avatar_frame(s,100,1,false));
    s.mood=node::Mood::Frightened;TEST_ASSERT_EQUAL(37,node::avatar_frame(s,100,1,false));
}
void calm_and_injury_frames() {
    node::AvatarState s;
    for(unsigned t=0;t<20000;t+=125) TEST_ASSERT_TRUE(node::avatar_frame(s,t,123,false)==32 || node::avatar_frame(s,t,123,false)==33 || node::avatar_frame(s,t,123,false)==39);
    s.set(node::Activity::Idle,node::Attention::Calm,node::Mood::Neutral,0,60,0);
    TEST_ASSERT_TRUE(node::avatar_frame(s,100,123,false)>=32);
    TEST_ASSERT_LESS_THAN(8,node::avatar_frame(s,100,123,true));
    s.set(node::Activity::Sleeping,node::Attention::Calm,node::Mood::Neutral,-1,60,0);
    TEST_ASSERT_EQUAL(42,node::avatar_frame(s,100,123,false));
}
int main(){UNITY_BEGIN();RUN_TEST(expires_across_wrap);RUN_TEST(sleeping_validation_atomic);RUN_TEST(bounded_requests);RUN_TEST(calm_and_injury_frames);RUN_TEST(expression_semantics);return UNITY_END();}
