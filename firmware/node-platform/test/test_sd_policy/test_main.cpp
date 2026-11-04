#include <unity.h>
#include "sd_policy.h"
#include "maintenance_gate.h"
void setUp() {} void tearDown() {}
void binds_card_and_geometry() {
    node::SdIdentity a{27,21325,48,312,1234,64021856256ULL,512,{1,2,3,4,5,0,0,0}};
    auto b=a;
    TEST_ASSERT_TRUE(node::same_card(a,b));
    b.serial++; TEST_ASSERT_FALSE(node::same_card(a,b)); b=a;
    b.bytes/=2; TEST_ASSERT_FALSE(node::same_card(a,b)); b=a;
    b.name[4]++; TEST_ASSERT_FALSE(node::same_card(a,b));
    char token[97]; node::sd_identity_text(a,token,sizeof(token));
    TEST_ASSERT_EQUAL(80,strlen(token));
}
void permit_is_fresh_single_use_and_exact() {
    node::SdPermit p; node::SdIdentity a{27,21325,48,312,1234,32000000000ULL,512,{1}};
    const char* token="0123456789abcdef0123456789abcdef";
    TEST_ASSERT_FALSE(p.consume(a,token,100));
    p.prepare(a,token,100);
    TEST_ASSERT_FALSE(p.consume(a,"ffffffffffffffffffffffffffffffff",101));
    p.prepare(a,token,100);
    auto b=a;b.serial++;
    TEST_ASSERT_FALSE(p.consume(b,token,101));
    TEST_ASSERT_FALSE(p.consume(a,token,102)); // mismatch invalidates authority
    p.prepare(a,token,100); TEST_ASSERT_TRUE(p.consume(a,token,101));
    TEST_ASSERT_FALSE(p.consume(a,token,102));
    p.prepare(a,token,100); TEST_ASSERT_FALSE(p.consume(a,token,120100));
}
void rejects_unknown_and_unsupported_geometry() {
    node::SdIdentity a{}; TEST_ASSERT_FALSE(node::sd_supported(a));
    a.bytes=64021856256ULL;a.sector=512; TEST_ASSERT_TRUE(node::sd_supported(a));
    a.sector=4096;TEST_ASSERT_FALSE(node::sd_supported(a));
}
void test_pattern_changes_with_address_and_run() {
    TEST_ASSERT_NOT_EQUAL(node::sd_pattern(0,17),node::sd_pattern(1024ULL*1024*1024,17));
    TEST_ASSERT_NOT_EQUAL(node::sd_pattern(0,17),node::sd_pattern(0,18));
    TEST_ASSERT_EQUAL(node::sd_pattern(1234,17),node::sd_pattern(1234,17));
}
void maintenance_is_exclusive() {
    node::MaintenanceGate gate;
    using O=node::MaintenanceOwner;
    TEST_ASSERT_TRUE(gate.claim(O::Storage));
    TEST_ASSERT_FALSE(gate.claim(O::Ota));
    gate.release(O::Ota);
    TEST_ASSERT_FALSE(gate.claim(O::Ota));
    gate.release(O::Storage);
    TEST_ASSERT_TRUE(gate.claim(O::Ota));
    TEST_ASSERT_FALSE(gate.claim(O::Storage));
}
int main(){UNITY_BEGIN();RUN_TEST(binds_card_and_geometry);RUN_TEST(permit_is_fresh_single_use_and_exact);RUN_TEST(rejects_unknown_and_unsupported_geometry);RUN_TEST(test_pattern_changes_with_address_and_run);RUN_TEST(maintenance_is_exclusive);return UNITY_END();}
