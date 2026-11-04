#include <unity.h>
#include "node_model.h"
#include "pixel_ui.h"
void setUp() {} void tearDown() {}
void labels() { TEST_ASSERT_TRUE(node::valid_label("A1")); TEST_ASSERT_TRUE(node::valid_label("D4")); TEST_ASSERT_FALSE(node::valid_label("E1")); TEST_ASSERT_FALSE(node::valid_label("A10")); TEST_ASSERT_FALSE(node::valid_label("a1")); }
void brightness() { TEST_ASSERT_EQUAL(0,node::brightness(-1)); TEST_ASSERT_EQUAL(63,node::brightness(25)); TEST_ASSERT_EQUAL(127,node::brightness(50)); TEST_ASSERT_EQUAL(127,node::brightness(100)); }
void framing() { node::LineBuffer b; for(int i=0;i<1100;i++) b.push('x'); TEST_ASSERT_EQUAL(node::LineBuffer::Overflow,b.push('\n')); TEST_ASSERT_EQUAL(node::LineBuffer::More,b.push('{')); TEST_ASSERT_EQUAL(node::LineBuffer::More,b.push('}')); TEST_ASSERT_EQUAL(node::LineBuffer::Ready,b.push('\n')); TEST_ASSERT_EQUAL_STRING("{}",b.data()); }
void sensor_crc() { const uint8_t bytes[]={0xBE,0xEF}; TEST_ASSERT_EQUAL(0x92,node::crc8(bytes,2)); }
void pixel_layout() {
    node::Frame f; f.text(4,2,"D4",3,0xffff); TEST_ASSERT_FALSE(f.clipped);
    f.text(2,58,"SD PENDING",1,0xffff); TEST_ASSERT_FALSE(f.clipped);
    int lit=0; for(auto px:f.pixels) if(px) lit++; TEST_ASSERT_GREATER_THAN(100,lit);
    f.text(62,62,"A1",1,0xffff); TEST_ASSERT_TRUE(f.clipped);
}
int main() { UNITY_BEGIN(); RUN_TEST(labels); RUN_TEST(brightness); RUN_TEST(framing); RUN_TEST(sensor_crc); RUN_TEST(pixel_layout); return UNITY_END(); }
