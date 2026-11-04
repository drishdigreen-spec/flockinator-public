#pragma once
#include "display_state.h"
namespace node {
struct RandomExpression {
    bool enabled=false;
    unsigned choice=0;
    uint32_t changes=0;
    void start(uint32_t now,uint32_t seed,AvatarState& state) {
        rng=seed?seed:1; enabled=true; changes=0; select(now,state);
    }
    void stop() { enabled=false; }
    void tick(uint32_t now,AvatarState& state) {
        if(enabled && !state.active(now)) select(now,state);
    }
private:
    uint32_t rng=1;
    uint32_t next() { rng^=rng<<13; rng^=rng>>17; rng^=rng<<5; return rng; }
    void select(uint32_t now,AvatarState& state) {
        // Cosmetic PRNG only; never used for authentication or experiments.
        choice=changes?(choice+1+next()%8)%9:next()%9;
        Activity activity=Activity::Idle; Attention attention=Attention::Calm; Mood mood=Mood::Neutral;
        switch(choice) {
            case 1:mood=Mood::Curious;break;
            case 2:mood=Mood::Content;break;
            case 3:activity=Activity::Sleeping;break;
            case 4:activity=Activity::Listening;attention=Attention::Attentive;break;
            case 5:activity=Activity::Processing;break;
            case 6:activity=Activity::Waiting;mood=Mood::Curious;break;
            case 7:activity=Activity::Speaking;break;
            case 8:mood=Mood::Frightened;attention=Attention::Urgent;break;
        }
        state.set(activity,attention,mood,-1,7,now);
        state.duration=3000+next()%4001;state.demo=true;changes++;
    }
};
}
