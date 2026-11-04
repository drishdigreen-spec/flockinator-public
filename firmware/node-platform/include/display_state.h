#pragma once
#include <cstdint>
namespace node {
enum class Activity:uint8_t { Sleeping,Idle,Listening,Processing,Waiting,Speaking };
enum class Attention:uint8_t { Calm,Attentive,Urgent };
enum class Mood:uint8_t { Neutral,Curious,Content,Frightened };
inline const char* activity_name(Activity a) { const char* n[]={"sleeping","idle","listening","processing","waiting","speaking"};return unsigned(a)<6?n[unsigned(a)]:"unknown"; }
inline const char* attention_name(Attention a) { const char* n[]={"calm","attentive","urgent"};return unsigned(a)<3?n[unsigned(a)]:"unknown"; }
inline const char* mood_name(Mood a) { const char* n[]={"neutral","curious","content","frightened"};return unsigned(a)<4?n[unsigned(a)]:"unknown"; }
struct AvatarState {
    Activity activity=Activity::Idle;
    Attention attention=Attention::Calm;
    Mood mood=Mood::Neutral;
    int vitality=-1;
    uint32_t started=0,duration=0;
    bool demo=false;
    bool active(uint32_t now) const { return duration && uint32_t(now-started)<duration; }
    void expire(uint32_t now) { if(duration && !active(now)) *this=AvatarState{}; }
    uint32_t remaining(uint32_t now) const {return active(now)?duration-uint32_t(now-started):0;}
    bool set(Activity a,Attention t,Mood m,int v,unsigned seconds,uint32_t now) {
        if(unsigned(a)>5 || unsigned(t)>2 || unsigned(m)>3 || v < -1 || v>4 || seconds<1 || seconds>300) return false;
        if(a==Activity::Sleeping && (t!=Attention::Calm || m==Mood::Frightened)) return false;
        activity=a;attention=t;mood=m;vitality=v;started=now;duration=seconds*1000;demo=false;return true;
    }
};
inline unsigned avatar_frame(const AvatarState& s,uint32_t now,uint32_t seed,bool injury) {
    const bool active=s.active(now);
    if(active && s.activity==Activity::Sleeping) return 42;
    unsigned base=32;
    if(injury && active && s.vitality>=0) base=unsigned(s.vitality)*8;
    if(active && s.mood==Mood::Frightened)return base+5;
    if(active && s.mood==Mood::Content)return base+2;
    if(active && s.activity==Activity::Speaking)return base+((now/180)%2?5:7);
    if(active && s.attention!=Attention::Calm)return base+7;
    // A long forward dwell followed by one short side glance. Seed varies nodes.
    unsigned cycle=3000+(seed%2000),phase=(now+seed%cycle)%cycle;
    return base+(phase<cycle-600?7:((now/cycle+seed)&1?0:1));
}
}
