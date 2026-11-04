#include <unity.h>
#include <vector>
#include "refresh_regions.h"
using namespace flockinator;

void unchanged_frame_has_no_region() {
    std::vector<uint8_t> pixels(kWidth*kHeight/2,0xff);
    const auto r=changed_region(pixels.data(),pixels.data());
    TEST_ASSERT_EQUAL(0,r.w);
    TEST_ASSERT_EQUAL(0,r.h);
}
void changed_pixels_align_and_include_erasure() {
    std::vector<uint8_t> before(kWidth*kHeight/2,0xff), after=before;
    after[100*kWidth/2+5/2]=0x0f;
    before[105*kWidth/2+17/2]=0x00; // Erased pixels also need refreshing.
    const auto r=changed_region(before.data(),after.data());
    TEST_ASSERT_EQUAL(4,r.x); TEST_ASSERT_EQUAL(100,r.y);
    TEST_ASSERT_EQUAL(16,r.w); TEST_ASSERT_EQUAL(6,r.h);
}
void edge_changes_stay_inside_panel() {
    std::vector<uint8_t> before(kWidth*kHeight/2,0xff), after=before;
    after.back()=0;
    auto r=changed_region(before.data(),after.data());
    TEST_ASSERT_EQUAL(956,r.x); TEST_ASSERT_EQUAL(539,r.y);
    TEST_ASSERT_EQUAL(4,r.w); TEST_ASSERT_EQUAL(1,r.h);
    after[0]=0;
    r=changed_region(before.data(),after.data());
    TEST_ASSERT_EQUAL(0,r.x); TEST_ASSERT_EQUAL(0,r.y);
    TEST_ASSERT_EQUAL(kWidth,r.w); TEST_ASSERT_EQUAL(kHeight,r.h);
}
void region_pixels_are_packed_without_full_screen_stride() {
    std::vector<uint8_t> pixels(kWidth*kHeight/2,0xff);
    const Rect r{4,12,8,2};
    for(int y=0;y<2;y++) for(int x=0;x<4;x++) pixels[(y+12)*kWidth/2+2+x]=y*10+x;
    uint8_t packed[10]={99,0,0,0,0,0,0,0,0,99};
    pack_region(pixels.data(),r,packed+1);
    const uint8_t expected[]={99,0,1,2,3,10,11,12,13,99};
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected,packed,10);
}
void full_clear_only_for_initial_page_manual_or_sleep() {
    TEST_ASSERT_TRUE(require_full_refresh(false,Page::Overview,Page::Overview,false,false));
    TEST_ASSERT_TRUE(require_full_refresh(true,Page::Overview,Page::Detail,false,false));
    TEST_ASSERT_TRUE(require_full_refresh(true,Page::Overview,Page::Overview,true,false));
    TEST_ASSERT_TRUE(require_full_refresh(true,Page::Overview,Page::Sleeping,false,true));
    TEST_ASSERT_FALSE(require_full_refresh(true,Page::Overview,Page::Overview,false,false));
}
void refresh_button_requests_full_clear() {
    Console c; c.page=Page::Overview;
    const auto r=button_rect(3);
    TEST_ASSERT_EQUAL(Action::Refresh,c.tap({r.x+2,r.y+2}));
}
int main(){ UNITY_BEGIN();
    RUN_TEST(unchanged_frame_has_no_region);
    RUN_TEST(changed_pixels_align_and_include_erasure);
    RUN_TEST(edge_changes_stay_inside_panel);
    RUN_TEST(region_pixels_are_packed_without_full_screen_stride);
    RUN_TEST(full_clear_only_for_initial_page_manual_or_sleep);
    RUN_TEST(refresh_button_requests_full_clear);
    return UNITY_END();
}
