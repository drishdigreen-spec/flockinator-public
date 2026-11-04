#pragma once
#include <cstdint>
#include <cstring>
#include <cmath>
#include "pixel_ui.h"
namespace ripple {
constexpr uint32_t Lifetime=1600,AckDeadline=1200;
inline int index(const char* label){return label&&std::strlen(label)==2&&label[0]>='A'&&label[0]<='D'&&label[1]>='1'&&label[1]<='4'?(label[1]-'1')*4+label[0]-'A':-1;}
inline bool neighbour(int a,int b){return a>=0&&a<16&&b>=0&&b<16&&std::abs(a%4-b%4)+std::abs(a/4-b/4)==1;}
struct Packet {uint8_t kind=0,from=0,to=0;uint32_t boot=0,sequence=0;};
inline void put(uint8_t* b,uint32_t v){for(unsigned i=0;i<4;i++)b[i]=v>>(i*8);}
inline uint32_t get(const uint8_t* b){return uint32_t(b[0])|uint32_t(b[1])<<8|uint32_t(b[2])<<16|uint32_t(b[3])<<24;}
inline void encode(const Packet& p,uint8_t b[16]){std::memcpy(b,"RPL1",4);b[4]=p.kind;b[5]=p.from;b[6]=p.to;b[7]=0;put(b+8,p.boot);put(b+12,p.sequence);}
inline bool decode(const uint8_t* b,size_t n,Packet& p){
 if(!b||n!=16||std::memcmp(b,"RPL1",4)||b[7]||b[4]<1||b[4]>2||!neighbour(b[5],b[6])||!get(b+8)||!get(b+12))return false;
 p={b[4],b[5],b[6],get(b+8),get(b+12)};return true;
}
struct Seen {
 uint32_t boot=0,sequence=0;
 bool accept(uint32_t b,uint32_t s){if(!b||!s)return false;if(b==boot&&int32_t(s-sequence)<=0)return false;boot=b;sequence=s;return true;}
};
struct Pending {
 bool active=false;uint8_t peer=0;uint32_t boot=0,sequence=0,at=0;
 void start(uint8_t p,uint32_t b,uint32_t s,uint32_t now){active=true;peer=p;boot=b;sequence=s;at=now;}
 bool matches(const Packet& p,uint32_t now)const{return active&&p.kind==2&&p.from==peer&&p.boot==boot&&p.sequence==sequence&&uint32_t(now-at)<AckDeadline;}
};
enum class EventKind {Departure,Arrival,Confirmed};
struct Event {bool active=false;uint8_t peer=0;EventKind kind=EventKind::Departure;uint32_t at=0;};
inline void add(node::Frame& f,int x,int y,unsigned r,unsigned g,unsigned b){
 if(x<0||x>=64||y<0||y>=64)return;
 auto& pixel=f.pixels[y*64+x];
 r=std::min(31u,r+unsigned(pixel>>11));g=std::min(63u,g+unsigned((pixel>>5)&63));b=std::min(31u,b+unsigned(pixel&31));
 pixel=uint16_t(r<<11|g<<5|b);
}
inline void draw(node::Frame& f,const Event& e,int own,uint32_t now){
 uint32_t age=now-e.at;if(!e.active||age>=Lifetime||!neighbour(own,e.peer))return;
 int dx=e.peer%4-own%4,dy=e.peer/4-own/4;
 float ex=31.5f+dx*31.5f,ey=31.5f+dy*31.5f;
 float fade=1.0f-float(age)/Lifetime;
 if(e.kind==EventKind::Departure){
  float t=std::min(1.0f,float(age)/600);float cx=31.5f+(ex-31.5f)*t,cy=31.5f+(ey-31.5f)*t;
  for(int y=0;y<64;y++)for(int x=0;x<64;x++){float d=(x-cx)*(x-cx)+(y-cy)*(y-cy);if(d<20)add(f,x,y,unsigned(31*fade),unsigned(38*fade),0);}
 }else if(e.kind==EventKind::Arrival){
  float radius=float(age)*0.045f;
  for(int y=0;y<64;y++)for(int x=0;x<64;x++){float dist=std::sqrt((x-ex)*(x-ex)+(y-ey)*(y-ey));float a=std::max(0.0f,1-std::abs(dist-radius)/3.0f)*fade;if(a>0)add(f,x,y,0,unsigned(55*a),unsigned(31*a));}
 }else{
  for(int i=18;i<46;i++){int x=dx?int(ex):i,y=dy?int(ey):i;add(f,x,y,0,unsigned(63*fade),0);}
 }
}
}
