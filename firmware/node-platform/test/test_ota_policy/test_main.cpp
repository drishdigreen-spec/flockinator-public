#include <unity.h>
#include "ota_policy.h"

void setUp() {}
void tearDown() {}
void reject_incompatible_before_flash() {
    uint8_t body[73]{};
    flockwire::put32(body,288); memcpy(body+68,"WS32",4); body[72]=1;
    TEST_ASSERT_TRUE(node::valid_manifest(body,sizeof(body),8*1024*1024));
    TEST_ASSERT_FALSE(node::valid_manifest(body,72,8*1024*1024));
    TEST_ASSERT_FALSE(node::valid_manifest(body,sizeof(body),287));
    body[68]='L'; TEST_ASSERT_FALSE(node::valid_manifest(body,sizeof(body),8*1024*1024)); body[68]='W';
    body[72]=2; TEST_ASSERT_FALSE(node::valid_manifest(body,sizeof(body),8*1024*1024)); body[72]=1;
    flockwire::put32(body,287); TEST_ASSERT_FALSE(node::valid_manifest(body,sizeof(body),8*1024*1024));
    flockwire::put32(body,8*1024*1024+1); TEST_ASSERT_FALSE(node::valid_manifest(body,sizeof(body),8*1024*1024));
}
void reject_other_chip_header() {
    uint8_t bytes[128]{}; bytes[0]=0xe9; bytes[12]=9;
    TEST_ASSERT_TRUE(node::valid_first_chunk(bytes,sizeof(bytes)));
    TEST_ASSERT_FALSE(node::valid_first_chunk(bytes,23));
    bytes[12]=0; TEST_ASSERT_FALSE(node::valid_first_chunk(bytes,sizeof(bytes)));
    bytes[12]=9; bytes[0]=0; TEST_ASSERT_FALSE(node::valid_first_chunk(bytes,sizeof(bytes)));
}
void timeout_survives_millis_wrap() {
    TEST_ASSERT_FALSE(node::link_expired(19999,0));
    TEST_ASSERT_TRUE(node::link_expired(20000,0));
    const uint32_t started=UINT32_MAX-10000;
    TEST_ASSERT_FALSE(node::link_expired(started+19999,started));
    TEST_ASSERT_TRUE(node::link_expired(started+20000,started));
}
void transfer_rejects_gaps_and_truncation() {
    flockwire::TransferOrder order;
    order.begin(300);
    TEST_ASSERT_EQUAL(flockwire::Decision::Reject,order.accept(3,0,128));
    TEST_ASSERT_EQUAL(flockwire::Decision::Reject,order.accept(2,1,128));
    TEST_ASSERT_EQUAL(flockwire::Decision::Write,order.accept(2,0,128));
    order.written(2,0,128);
    TEST_ASSERT_EQUAL(flockwire::Decision::Duplicate,order.accept(2,0,128));
    TEST_ASSERT_EQUAL(flockwire::Decision::Reject,order.accept(2,0,127));
    TEST_ASSERT_FALSE(order.complete());
    order.written(3,128,128);
    TEST_ASSERT_EQUAL(flockwire::Decision::Reject,order.accept(4,256,45));
    TEST_ASSERT_EQUAL(flockwire::Decision::Write,order.accept(4,256,44));
    order.written(4,256,44);
    TEST_ASSERT_TRUE(order.complete());
    TEST_ASSERT_EQUAL(flockwire::Decision::Reject,order.accept(5,300,1));
}
int main() {
    UNITY_BEGIN(); RUN_TEST(reject_incompatible_before_flash); RUN_TEST(reject_other_chip_header);
    RUN_TEST(timeout_survives_millis_wrap); RUN_TEST(transfer_rejects_gaps_and_truncation); return UNITY_END();
}
