#pragma once
#include "world_render.h"
namespace survey {
constexpr const char* States[]={"READY","TAKEOFF","TRANSIT","SURVEY","RETURN","LAND","CHARGING","UNAVAIL"};
struct Packet {
 uint32_t run=0,seq=0,time=0;int node=0,state=0,energy=0,distance=-1,reserve=0;
 world::Pose pose{};world::Peer peers[3]{};int peerCount=0;
};
inline bool finite(float n,float bound){return std::isfinite(n)&&std::abs(n)<=bound;}
inline bool position(world::Vec p){return finite(p.x,10000)&&finite(p.y,10000)&&finite(p.z,1000)&&p.z>=0;}
inline bool valid(const Packet& p,int node){
 if(!p.run||!p.seq||p.node!=node||node<0||node>15||p.state<0||p.state>7||p.energy<0||p.energy>10000||p.distance< -1||p.distance>99999||p.reserve<0||p.reserve>2||p.peerCount<0||p.peerCount>3)return false;
 if(!position(p.pose.position)||!finite(p.pose.heading,360)||!finite(p.pose.pitch,90)||!finite(p.pose.roll,360))return false;
 for(int i=0;i<p.peerCount;i++){const auto& peer=p.peers[i];if(peer.id<0||peer.id>15||peer.id==node||!position(peer.position))return false;for(int j=0;j<i;j++)if(peer.id==p.peers[j].id)return false;}
 return true;
}
struct Runtime {
 bool active=false,seen=false;Packet latest{};world::Pose from{};uint32_t received=0,blendMs=500;
 world::Sample sample(uint32_t now)const{
  auto pose=world::mix(from,latest.pose,world::clamp(uint32_t(now-received)/float(blendMs)));
  return {pose,latest.time,0,world::Air,uint32_t(now-received)>=2000?world::Stale:world::Live};
 }
 bool receive(const Packet& p,int node,uint32_t now){
  if(!valid(p,node)||(seen&&(p.run<latest.run||(p.run==latest.run&&(p.seq<=latest.seq||p.time<latest.time)))))return false;
  bool reset=!seen||p.run!=latest.run;
  from=reset?p.pose:sample(now).pose;blendMs=!reset&&uint32_t(now-received)>=2000?750:500;
  latest=p;received=now;active=seen=true;return true;
 }
};
inline void render(node::Frame& f,const Runtime& r,uint32_t now,world::Sensor sensor){
 const auto& v=r.latest;auto s=r.sample(now);
 // A non-null empty peer list deliberately suppresses fixture-generated peers.
 world::render(f,s,v.node,sensor,v.peers,v.peerCount);recon::Painter p{f};char text[24];
 p.rect(49,0,15,7,recon::bg);
 if(v.distance<0)std::snprintf(text,sizeof(text),"D--");else std::snprintf(text,sizeof(text),"%03d",std::min(999,v.distance));
 p.text(50,1,text,recon::accent);
 p.rect(0,51,64,13,recon::bg);p.text(2,52,s.freshness==world::Stale?"STALE":States[v.state],recon::ink);
 p.text(44,52,v.reserve==2?"RTN":v.reserve==1?"LOW":"OK",recon::dim);
 std::snprintf(text,sizeof(text),"ALT %d",int(std::lround(s.pose.position.z)));p.text(2,58,text,recon::dim);
 std::snprintf(text,sizeof(text),"E%03d",(v.energy+50)/100);p.text(46,58,text,recon::dim);
}
} // namespace survey
