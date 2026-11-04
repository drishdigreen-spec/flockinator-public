#include "../main/lab_model.h"
#include <cassert>
#include <cstdio>
#include <cstring>

// Desktop Random(string) begins with SHA-512 of each of these seed strings.
// Inject only the digest so this regression runs without the ESP crypto SDK.
struct Vector { const char* name; const char* digest; };
static const Vector seeds[] = {
    {"field-signals-v1/11/codebooks","40af38d9c3562741207c2fdb7053230a33bb24569ee09e52d0136771fe1d12c9e4d5a9a97326b19f5370a70a4dafc427f489490d4558611574adad23969dc47d"},
    {"field-signals-v1/11/train","38e37ca5b35affbe8736be7b371ebb89131741697a15c0dcfe7162c78b559890b16c6a9197f2b0a2dd0b863f8a421fb596bd4055ce5f1b143ca9cba08c5db967"},
    {"field-signals-v1/11/test","e60e0911042fb030f2308b7e11318687a2af686527a566b73ee34c1defadc2f63db35e110b19a582c7a1b7fe294a01d2b76bc7249fb6ff4abd4a69d8d75913b5"},
    {"field-signals-v1/90/codebooks","c1b0d11cb86fd3de9e2e7e1b217c6bbc8e0df7ce88192accba0e77b88e745a88fe823c3f08d1770c510af96c55655896c377e1a4d6860c4c4ab3a74650d16ed5"},
    {"field-signals-v1/90/train","522cdf281388171fa1b0ab8e4bf564153d543e2cdef884b96471763de8b51ef3b1bd8ad2b09e93d05473ce6ccae21c7426737e24fa358d50bbec59632a1bd698"},
    {"field-signals-v1/90/test","d31ca2d37186219a77b5e4ac1c7c8d5c3124287316716034a5fd1413bdca79e2384eb1e75d33daccebccedd94a5a7009b3d725d6bedadb93ec2b7cad399d5774"},
};
static bool digest(const char* input,unsigned char* output){
    for(const auto& v:seeds)if(!strcmp(input,v.name)){
        for(int i=0;i<64;i++){
            unsigned byte;
            if(sscanf(v.digest+2*i,"%2x",&byte)!=1)return false;
            output[i]=static_cast<unsigned char>(byte);
        }
        return true;
    }
    return false;
}
static void check(signals::Model& m,unsigned seed,signals::Link link,const int expected[5]){
    assert(m.init(seed,link,digest));
    for(int i=0;i<signals::Train+signals::Test;i++)m.step();
    for(int i=0;i<4;i++)assert(m.scores[i].recovered==expected[i]);
    assert(m.solo.recovered==expected[4]);
    assert(m.turn==80);
    m.step();assert(m.turn==80);
}
int main(){
    signals::Model m{};
    const int a[]={101,42,42,49,73},b[]={96,87,96,84,72};
    check(m,11,signals::Scrambled,a);
    check(m,90,signals::HalfLost,b);
}
