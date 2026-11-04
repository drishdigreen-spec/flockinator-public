#pragma once
#include "pixel_ui.h"
#include "display_state.h"
#include <cstdio>
namespace node {
inline void avatar_render(Frame& f,const uint8_t* pixels,const char* label,const AvatarState& request,uint32_t now,uint32_t seed,bool warning,bool wifi,bool peer,bool sd){
 f.clear();if(pixels)for(unsigned i=0;i<4096;i++)f.pixels[i]=uint16_t(pixels[i*2])|(uint16_t(pixels[i*2+1])<<8);
 const bool active=request.active(now);
 // Clear small overlays only; keep eyes and mouth unobscured.
 for(int y=0;y<7;y++)for(int x=0;x<64;x++)f.pixel(x,y,0);
 for(int y=57;y<64;y++)for(int x=0;x<64;x++)f.pixel(x,y,0);
 f.text(1,1,label,1,0xffff);
 const char* state=warning?"WARN":active?request.demo?"DEMO":"EXP":"IDLE";
 f.text(42,1,state,1,warning?0xffe0:0x07ff);
 if(active){
  const char* text=request.activity==Activity::Sleeping?"SLEEP":request.activity==Activity::Processing?"WORK":request.activity==Activity::Listening?"LISTEN":request.activity==Activity::Waiting?"WAIT":request.activity==Activity::Speaking?"TALK":request.mood==Mood::Content?"HAPPY":request.mood==Mood::Frightened?"FEAR":request.mood==Mood::Curious?"CURIOUS":"IDLE";
  f.text(18,58,text,1,0xffff);
  if(request.activity==Activity::Processing){for(unsigned i=0;i<3;i++)f.pixel(30+i*3,54,((now/250)%3)==i?0x07ff:0x2104);}
 }else f.text(18,58,"CALM",1,0xffff);
 f.text(1,58,"W",1,wifi?0x07e0:0xffe0);f.text(6,58,"P",1,peer?0x07e0:0x4208);f.text(60,58,"S",1,sd?0x07e0:0xffe0);
 (void)seed;
}
}
