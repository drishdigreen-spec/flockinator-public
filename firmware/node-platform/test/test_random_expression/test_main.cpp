#include <unity.h>
#include "random_expression.h"
void setUp() {} void tearDown() {}
void bounded_valid_choices_without_repeats() {
    node::RandomExpression random; node::AvatarState state;
    uint32_t now=100; random.start(now,123,state);
    unsigned seen=0;
    for(unsigned i=0;i<200;i++) {
        unsigned previous=random.choice;
        seen|=1u<<previous;
        TEST_ASSERT_TRUE(state.demo); TEST_ASSERT_TRUE(state.active(now));
        TEST_ASSERT_TRUE(state.duration>=3000 && state.duration<=7000);
        TEST_ASSERT_EQUAL(-1,state.vitality);
        if(state.activity==node::Activity::Sleeping) {
            TEST_ASSERT_EQUAL(int(node::Attention::Calm),int(state.attention));
            TEST_ASSERT_EQUAL(int(node::Mood::Neutral),int(state.mood));
        }
        random.tick(now+state.duration-1,state);
        TEST_ASSERT_EQUAL(previous,random.choice);
        now+=state.duration; random.tick(now,state);
        TEST_ASSERT_NOT_EQUAL(previous,random.choice);
    }
    TEST_ASSERT_EQUAL(0x1ff,seen);
    TEST_ASSERT_EQUAL(201,random.changes);
}
void deterministic_and_node_specific() {
    node::RandomExpression a,b,c; node::AvatarState x,y,z;
    a.start(0,123,x); b.start(0,123,y); c.start(0,456,z);
    bool differed=false;
    for(unsigned t=0;t<120000;t+=100) {
        a.tick(t,x); b.tick(t,y); c.tick(t,z);
        TEST_ASSERT_EQUAL(a.choice,b.choice); TEST_ASSERT_EQUAL(x.duration,y.duration);
        differed|=a.choice!=c.choice || x.duration!=z.duration;
    }
    TEST_ASSERT_TRUE(differed);
}
void wraps_and_stops() {
    node::RandomExpression r; node::AvatarState s;
    r.start(0xfffffff0,0,s); auto duration=s.duration;
    r.tick(uint32_t(0xfffffff0+duration-1),s); TEST_ASSERT_EQUAL(1,r.changes);
    r.tick(uint32_t(0xfffffff0+duration),s); TEST_ASSERT_EQUAL(2,r.changes);
    r.stop(); r.tick(100000,s); TEST_ASSERT_FALSE(r.enabled); TEST_ASSERT_EQUAL(2,r.changes);
}
void expired_lease_cannot_reappear_after_full_counter_cycle() {
    node::AvatarState s;
    s.set(node::Activity::Speaking,node::Attention::Calm,node::Mood::Neutral,-1,2,100);
    s.expire(2100);
    TEST_ASSERT_FALSE(s.active(100)); TEST_ASSERT_EQUAL(0,s.duration);
}
int main(){UNITY_BEGIN();RUN_TEST(bounded_valid_choices_without_repeats);RUN_TEST(deterministic_and_node_specific);RUN_TEST(wraps_and_stops);RUN_TEST(expired_lease_cannot_reappear_after_full_counter_cycle);return UNITY_END();}
