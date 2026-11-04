#pragma once
#include <cstdint>
namespace signals {
constexpr int Units=16, Train=48, Test=32;
enum Link {Clear, Muted, HalfLost, Scrambled};
using Hash = bool(*)(const char*,unsigned char[64]);
struct Rng {
    uint32_t words[624]; int cursor;
    bool seed(uint32_t seed,const char* phase,Hash hash);
    void array_seed(const uint32_t* key,int length);
    uint32_t next();
    int below(int n);
    double fraction();
};
struct World { uint8_t truth[4],cue[Units],replacement[48]; bool lost[48]; };
struct Memory { uint8_t counts[Units][3][3][3]{}; };
struct Score { int correct=0,recovered=0,packets=0; };
struct Choice { uint8_t sector,token[3],decoded[3]; };
struct Model {
    Rng training,testing;
    uint8_t book[Units][3]{};
    Memory memory[2]{};
    World held[Test]{};
    Score scores[4]{},solo{};
    int turn=0, training_packets[2]{}, mappings[2]{},known[2]{};
    Link intervention=Scrambled;
    bool init(uint32_t seed,Link link,Hash hash);
    void step();
    Choice choose(const World&,int unit,int training_arm,Link test_link) const;
};
}
