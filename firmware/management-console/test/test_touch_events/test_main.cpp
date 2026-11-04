#include <unity.h>
#include "touch_events.h"
using namespace flockinator;
void stale_or_held_reports_do_not_repeat_a_tap() {
    TouchGesture gesture;
    TEST_ASSERT_FALSE(gesture.accept(false,true,{20,30}));
    TEST_ASSERT_TRUE(gesture.accept(true,true,{20,30}));
    TEST_ASSERT_FALSE(gesture.accept(true,true,{20,30}));
    TEST_ASSERT_FALSE(gesture.accept(false,false,{-1,-1})); // No data is not release.
    TEST_ASSERT_FALSE(gesture.accept(true,true,{20,30}));
    TEST_ASSERT_FALSE(gesture.accept(true,false,{-1,-1}));
    TEST_ASSERT_TRUE(gesture.accept(true,true,{20,30}));
}
void invalid_or_multiple_contacts_wait_for_release() {
    TouchGesture gesture;
    TEST_ASSERT_FALSE(gesture.accept(true,true,{-1,-1}));
    TEST_ASSERT_FALSE(gesture.accept(true,true,{20,30}));
    gesture.accept(true,false,{-1,-1});
    TEST_ASSERT_TRUE(gesture.accept(true,true,{20,30}));
}
void diagnostic_counters_cannot_trigger_an_automatic_redraw() {
    TEST_ASSERT_FALSE(automatic_updates(Page::Diagnostics));
    TEST_ASSERT_FALSE(automatic_updates(Page::Alignment));
    TEST_ASSERT_FALSE(automatic_updates(Page::Sleeping));
    TEST_ASSERT_TRUE(automatic_updates(Page::Overview));
    TEST_ASSERT_TRUE(automatic_updates(Page::Detail));
}
int main(){UNITY_BEGIN();
    RUN_TEST(stale_or_held_reports_do_not_repeat_a_tap);
    RUN_TEST(invalid_or_multiple_contacts_wait_for_release);
    RUN_TEST(diagnostic_counters_cannot_trigger_an_automatic_redraw);
    return UNITY_END();
}
