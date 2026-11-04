#pragma once
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <algorithm>
#include <type_traits>
#ifdef ESP_PLATFORM
#include "esp_heap_caps.h"
#include "esp_random.h"
#endif
inline constexpr float PI=3.14159265358979323846f,TWO_PI=2*PI,HALF_PI=PI/2;
using std::abs;
template<class A,class B> inline auto min(A a,B b){using C=std::common_type_t<A,B>;return std::min(C(a),C(b));}
template<class A,class B> inline auto max(A a,B b){using C=std::common_type_t<A,B>;return std::max(C(a),C(b));}
template<class A,class B,class C> inline auto constrain(A a,B b,C c){return min(max(a,b),c);}
inline uint32_t pattern_random_state=12345,pattern_now=0;
inline uint32_t pattern_random(){pattern_random_state^=pattern_random_state<<13;pattern_random_state^=pattern_random_state>>17;pattern_random_state^=pattern_random_state<<5;return pattern_random_state;}
#ifndef ESP_PLATFORM
inline uint32_t esp_random(){return pattern_random();}
#endif
inline long random(long n){return n>0?pattern_random()%n:0;}
inline long random(long a,long b){return a+random(b-a);}
inline void randomSeed(unsigned n){pattern_random_state=n?n:1;}
inline uint32_t millis(){return pattern_now;}
inline long map(long x,long a,long b,long c,long d){return b==a?c:(x-a)*(d-c)/(b-a)+c;}
namespace PFMem {
inline void* alloc(size_t n){
#ifdef ESP_PLATFORM
return heap_caps_calloc(1,n,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
#else
return calloc(1,n);
#endif
}
inline float* allocFloats(int n){return static_cast<float*>(alloc(size_t(n)*sizeof(float)));}
}
#include "core_noise.h"

#include "core_math.h"
#include "core_color.h"
#include "pf_params.h"
#include "pixel_ui.h"
#define PANEL_RES_W 64
#define PANEL_RES_H 64
struct InputFrame {
 long knobs[4]{}; bool btnHeld[4]{}; uint32_t now=0; int knobDeltas[4]{}; bool btnPressed[4]{};
 bool knobAudioActive[4]{}; float knobAudioValue[4]{};
 bool paramAbsoluteActive[4]{}; uint16_t paramAbsolute[4]{};
};
struct SilentPatternflowLog {
 void println(const char*) {}
 template<typename... Args> void printf(const char*, Args...) {}
};
inline SilentPatternflowLog PatternflowLog;
namespace PFCanvas {
inline node::Frame* target;
inline void setPixel(int x,int y,uint8_t r,uint8_t g,uint8_t b) {
 if(target && x>=0 && x<64 && y>=0 && y<64)
 target->pixels[y*64+x]=((r&248)<<8)|((g&252)<<3)|(b>>3);
}
inline void present() {}
}
#include "catalogue.h"
namespace patternflow_trial {
inline bool initialized[count]{};
inline bool ready=false;
inline unsigned current=0;
inline uint16_t parameters[4]{500,400,450,500};
inline unsigned bag[count]{},remaining=0;
inline unsigned next_pattern(){
 if(!remaining){for(unsigned i=0;i<count;i++)bag[i]=i;remaining=count;}
 unsigned pos=pattern_random()%remaining;unsigned next=bag[pos];
 if(remaining>1 && next==current){pos=(pos+1)%remaining;next=bag[pos];}
 bag[pos]=bag[--remaining];return next;
}
inline uint32_t switched=0,last=0,duration=30000,changes=0;
inline void select(unsigned i,uint32_t now){
 current=i%count;switched=now;changes++;
 for(auto& value:parameters)value=250+pattern_random()%501;
 if(!initialized[current]){patterns[current].setup();initialized[current]=true;}
 duration=25000+pattern_random()%20001;
}
inline void render(node::Frame& frame,uint32_t now,int index){
 pattern_now=now;PFCanvas::target=&frame;
 if(!ready){randomSeed(0x9e3779b9u^(uint32_t(index+1)*2654435761u)^now^esp_random());select(next_pattern(),now);ready=true;last=now;}
 if(uint32_t(now-switched)>=duration){select(next_pattern(),now);}
 float dt=std::min(0.1f,float(uint32_t(now-last))/1000.0f);last=now;
 InputFrame input{};input.now=now;
 for(unsigned i=0;i<4;i++){input.paramAbsoluteActive[i]=true;input.paramAbsolute[i]=parameters[i];}
 frame.clear();patterns[current].update(dt,input);patterns[current].draw();
 PFCanvas::target=nullptr;
}
}
