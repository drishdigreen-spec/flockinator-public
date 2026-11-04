#include <unity.h>
#include <vector>
#include <cstring>
#include "face_pack.h"
void setUp(){} void tearDown(){}
void validates_geometry(){
 std::vector<uint8_t> p(16+8192);std::memcpy(p.data(),"FLKFACE1",8);p[8]=1;p[13]=32;
 TEST_ASSERT_TRUE(node::valid_face_pack(p.data(),p.size()));
 TEST_ASSERT_FALSE(node::valid_face_pack(p.data(),p.size()-1));
 p[8]=65;TEST_ASSERT_FALSE(node::valid_face_pack(p.data(),p.size()));
 p[8]=1;p[0]='X';TEST_ASSERT_FALSE(node::valid_face_pack(p.data(),p.size()));
 TEST_ASSERT_FALSE(node::valid_face_pack(nullptr,0));
}
int main(){UNITY_BEGIN();RUN_TEST(validates_geometry);return UNITY_END();}
