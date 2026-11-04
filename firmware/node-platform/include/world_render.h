#pragma once
#include "recon_render.h"
#include <algorithm>
#include <cmath>
#include <cstdint>

// Browser World view port. Fictional local coordinates, no flight dynamics.
// +X east, +Y north, +Z up; clockwise heading, positive-up pitch.
namespace world {
constexpr uint32_t Seed = 271828;
constexpr float Pi = 3.14159265358979323846f;
struct Vec { float x,y,z; };
struct Pose { Vec position; float heading,pitch,roll; };
struct Basis { Vec forward,right,up; };
struct Projection { float x,y,horizontal,vertical; bool behind; };
enum Sensor { Cam, Night, WhiteHot, BlackHot, IR };
enum Stage { Air, Impact, Ground, Static };
enum Freshness { Live, Stale, Resync };
struct Sample { Pose pose; uint32_t time=0,age=0; Stage stage=Air; Freshness freshness=Live; };
inline float clamp(float x,float lo=0,float hi=1){return std::max(lo,std::min(hi,x));}
inline float wrap(float a){a=std::fmod(a,360.f);return a<0?a+360:a;}
inline float angle(float a,float b,float t){return wrap(a+(wrap(b-a+180)-180)*t);}
inline Vec mix(Vec a,Vec b,float t){return {a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,a.z+(b.z-a.z)*t};}
inline Pose mix(Pose a,Pose b,float t){return {mix(a.position,b.position,t),angle(a.heading,b.heading,t),a.pitch+(b.pitch-a.pitch)*t,angle(a.roll,b.roll,t)};}
inline float dot(Vec a,Vec b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline Basis basis(const Pose& p){
 float h=p.heading*Pi/180, pitch=p.pitch*Pi/180,r=p.roll*Pi/180;
 float sh=std::sin(h),ch=std::cos(h),sp=std::sin(pitch),cp=std::cos(pitch),sr=std::sin(r),cr=std::cos(r);
 Vec right{ch,-sh,0},up{-sh*sp,-ch*sp,cp};
 return {{sh*cp,ch*cp,sp},{right.x*cr+up.x*sr,right.y*cr+up.y*sr,up.z*sr},{up.x*cr-right.x*sr,up.y*cr-right.y*sr,up.z*cr}};
}
inline Projection project(const Pose& p,Vec point){
 auto b=basis(p);Vec delta{point.x-p.position.x,point.y-p.position.y,point.z-p.position.z};
 float depth=dot(delta,b.forward),h=dot(delta,b.right),v=dot(delta,b.up),d=std::max(depth,.001f);
 return {31.5f+42*h/d,28.5f-42*v/d,h,v,depth<=.001f};
}
inline Pose authored(int node,uint32_t ms){
 float t=ms/1000.f,a=t*.025f+node*.025f;
 return {{(node%4-1.5f)*18+80*(1-std::cos(a)),(node/4)*18.f+80*std::sin(a),20+(node/4)*3.f+std::sin(t*.15f+node)*2},a*180/Pi,-5+std::sin(t*.12f+node)*2,std::sin(t*.25f+node*.3f)*8};
}
inline Pose fixture(int node,uint32_t ms){
 uint32_t lower=ms/500*500;return mix(authored(node,lower),authored(node,lower+500),(ms-lower)/500.f);
}
struct Runtime {
 uint32_t elapsed=0,previous=0,latest=0,resumeAt=0,impactAt=0;
 bool paused=false,enabled=true,blending=false,impacted=false;
 Pose from{},entry{};
 void start(uint32_t now){*this=Runtime{};previous=now;}
 void tick(uint32_t now){if(!paused)elapsed+=uint32_t(now-previous);previous=now;if(enabled)latest=elapsed/500*500;}
 void pause(uint32_t now){tick(now);paused=true;}
 void play(uint32_t now){previous=now;paused=false;}
 void interrupt(uint32_t now){tick(now);enabled=false;}
 Sample sample(uint32_t now,int node){
  tick(now);uint32_t time=std::min(elapsed>500?elapsed-500:0,latest);
  Sample s{fixture(node,time),time,0,Air,elapsed-latest>=1500?Stale:Live};
  if(impacted){
   uint32_t effectTime=enabled?elapsed:std::max(impactAt,latest);
   s.age=effectTime-impactAt;float t=clamp(s.age/2000.f),e=t*t*(3-2*t);s.pose=entry;
   s.pose.position.z+=(.25f-entry.position.z)*e;s.pose.pitch+=(-90-entry.pitch)*e;s.pose.roll+=(node%2?-180:180)*e;
   s.stage=s.age<2000?Impact:s.age>=3000&&s.age<8000?Static:Ground;
  }
  if(blending){float t=clamp((elapsed-resumeAt)/750.f);s.pose=mix(from,s.pose,t);if(t<1&&s.freshness==Live)s.freshness=Resync;else if(t>=1)blending=false;}
  return s;
 }
 void resume(uint32_t now,int node){auto s=sample(now,node);from=s.pose;blending=s.freshness==Stale;resumeAt=elapsed;enabled=true;latest=elapsed/500*500;}
 bool impact(uint32_t now,int node){auto s=sample(now,node);if(impacted||!enabled||s.freshness!=Live)return false;entry=s.pose;impactAt=elapsed;impacted=true;return true;}
};
inline uint32_t hash(int32_t x,int32_t y,uint32_t seed){uint32_t n=uint32_t(x)*73856093u^uint32_t(y)*19349663u^seed;n=(n^(n>>16))*0x45d9f3bu;return n^(n>>16);}
inline int terrain(float x,float y){
 int gx=std::floor(x/24),gy=std::floor(y/24);uint32_t cell=hash(gx,gy,Seed);float lx=x-gx*24,ly=y-gy*24;
 return cell%4>0&&lx>3&&lx<20&&ly>3&&ly<20?2+cell%2:1;
}
inline uint16_t color(unsigned c,Sensor sensor){if(sensor==BlackHot)c=0xffffff-c;return recon::rgb(c);}
struct Marker { int x,y,lx,ly,width; char text[4]; bool rear,edge; };
struct Peer { int id; Vec position; };
inline void sightings(node::Frame& f,const Sample& s,int node,Sensor sensor,const Peer* peers=nullptr,int peerCount=0){
 if(s.stage!=Air||s.freshness==Stale)return;
 recon::Painter p{f};constexpr uint16_t cyan=recon::rgb(0x80dcf2);
 for(auto point:{Vec{0,100,0},Vec{40,160,0},Vec{-30,180,0}}){auto q=project(s.pose,point);if(!q.behind&&q.x>=1&&q.x<=62&&q.y>=9&&q.y<=48)p.pixel(q.x,q.y,sensor==WhiteHot?0:0xffff);}
 Marker markers[3]{};int count=0;
 int total=peers?peerCount:15;
 for(int entry=0;entry<(peers?peerCount:16)&&count<3;entry++){
  int id=peers?peers[entry].id:entry;
  if(id==node)continue;
  auto q=project(s.pose,peers?peers[entry].position:fixture(id,s.time).position);bool inside=!q.behind&&q.x>=1&&q.x<=62&&q.y>=9&&q.y<=48;
  if(!inside){float dx=q.horizontal,dy=-q.vertical;if(std::abs(dx)+std::abs(dy)<.00001f){dx=0;dy=1;}float scale=1/std::max(std::abs(dx)/30.5f,std::abs(dy)/19.5f);q.x=31.5f+dx*scale;q.y=28.5f+dy*scale;}
  Marker m{};m.x=std::lround(clamp(q.x,1,62));m.y=std::lround(clamp(q.y,9,48));m.rear=q.behind;m.edge=!inside;
  if(m.rear){m.text[0]='R';recon::label(id,m.text+1);}else recon::label(id,m.text);
  m.width=m.rear?11:7;bool placed=false;
  const int offsets[6][2]={{3,-6},{-m.width-3,-6},{3,3},{-m.width-3,3},{3,-13},{-m.width-3,10}};
  for(auto& off:offsets){
   m.lx=std::lround(clamp(m.x+off[0],1,63-m.width));m.ly=std::lround(clamp(m.y+off[1],9,44));
   if(m.lx<14&&m.ly+5>43)continue;
   bool overlap=false;for(int i=0;i<count;i++){auto& b=markers[i];if(!(m.lx>b.lx+b.width+1||b.lx>m.lx+m.width+1||m.ly>b.ly+6||b.ly>m.ly+6))overlap=true;}
   if(!overlap){placed=true;break;}
  }
  if(placed)markers[count++]=m;
 }
 for(int i=0;i<count;i++){auto& m=markers[i];if(!m.edge){p.pixel(m.x,m.y,cyan);p.pixel(m.x-1,m.y,cyan);p.pixel(m.x+1,m.y,cyan);}else{float dx=31.5f-m.x,dy=28.5f-m.y,l=std::sqrt(dx*dx+dy*dy);for(int t=0;t<7;t+=2)p.pixel(m.x+dx/l*t,m.y+dy/l*t,cyan);}}
 for(int i=0;i<count;i++){auto& m=markers[i];p.rect(m.lx,m.ly,m.width,5,recon::bg);p.text(m.lx,m.ly,m.text,cyan);}
 if(total>count){char omitted[5];std::snprintf(omitted,sizeof(omitted),"+%d",std::min(99,total-count));p.rect(1,44,12,5,recon::bg);p.text(1,44,omitted,cyan);}
}
inline const char* stage_name(Stage stage){return stage==Impact?"IMPACT":stage==Ground?"GROUND":stage==Static?"NO LINK":"SURVEY";}
inline const char* sensor_name(Sensor s){return s==Cam?"cam":s==Night?"night":s==WhiteHot?"whitehot":s==BlackHot?"blackhot":"ir";}
inline void render(node::Frame& f,const Sample& s,int node,Sensor sensor,const Peer* peers=nullptr,int peerCount=0){
 f.clear(recon::bg);auto b=basis(s.pose);
 const unsigned cam[]={0x5e7989,0x414c31,0x5d643e,0x7e764c,0xadc6cd},nv[]={0x06110d,0x102b20,0x244134,0x3a5945,0x92f5ad},wh[]={0x1c1c1c,0x404040,0x595959,0x717171,0x9b9b9b};
 const unsigned* table=sensor==Cam?cam:(sensor==WhiteHot||sensor==BlackHot)?wh:nv;
 for(int y=8;y<50;y++)for(int x=0;x<64;x++){
  if(s.stage==Static){unsigned v=24+hash(x,y,Seed+s.age/125)%88;f.pixel(x,y,recon::rgb(v*0x010101));continue;}
  float rx=(x-31.5f)/42,ry=(28.5f-y)/42;
  Vec d{b.forward.x+b.right.x*rx+b.up.x*ry,b.forward.y+b.right.y*rx+b.up.y*ry,b.forward.z+b.right.z*rx+b.up.z*ry};
  int shade=0;if(d.z<0){float t=-s.pose.position.z/d.z;shade=t<1800?terrain(s.pose.position.x+d.x*t,s.pose.position.y+d.y*t):1;}if(std::abs(d.z)<.008f)shade=4;
  unsigned c=table[shade];float blend=s.stage==Ground?1:s.stage==Impact?clamp((float(s.age)-1500)/500):0;
  if(blend){unsigned grain=hash(x/3+std::floor(s.pose.position.x*8),y/3+std::floor(s.pose.position.y*8),Seed)%4;const unsigned soil[]={0x33271b,0x493725,0x60472e,0x795b3b};unsigned earth=sensor==Cam?soil[grain]:table[1+grain%3],out=0;for(int shift:{0,8,16})out|=unsigned(std::lround(((c>>shift)&255)*(1-blend)+((earth>>shift)&255)*blend))<<shift;c=out;}
  f.pixel(x,y,color(c,sensor));
 }
 sightings(f,s,node,sensor,peers,peerCount);recon::Painter p{f};char text[24],id[3];recon::label(node,id);
 if(s.stage==Static){p.rect(8,25,48,11,0);p.text(10,28,"SIGNAL LOST",recon::rgb(0xe1e8e9));}
 p.text(2,1,id,recon::ink);float h=wrap(s.pose.heading)*Pi/180;
 // The north arrow points relative to this camera's supplied heading.
 float dx=-std::sin(h),dy=-std::cos(h),tx=14+dx*2,ty=3+dy*2;
 p.line(14-dx*2,3-dy*2,tx,ty,recon::ink);p.line(tx-dx*2-dy,ty-dy*2+dx,tx,ty,recon::ink);p.line(tx-dx*2+dy,ty-dy*2-dx,tx,ty,recon::ink);
 const char* sensors[]={"TV","NV","WH","BH","IR"};p.text(21,1,sensors[sensor],recon::dim);
 std::snprintf(text,sizeof(text),"%03u",unsigned(std::lround(wrap(s.pose.heading)))%360);p.text(33,1,text,recon::dim);p.text(50,1,"D--",recon::accent);p.line(1,7,62,7,recon::dim);
 const char* labels[]={"SURVEY","LOITER","SHARE","CHECK"};const char* label=s.stage==Air?labels[(s.time/8000)%4]:stage_name(s.stage);
 if(s.freshness==Stale)label="STALE";else if(s.freshness==Resync)label="RESYNC";
 p.line(1,50,62,50,recon::dim);p.text(2,52,label,recon::ink);p.text(38,52,"NR-:--",recon::dim);
 std::snprintf(text,sizeof(text),"ALT %d",int(std::lround(s.pose.position.z)));p.text(2,58,text,recon::dim);p.text(48,58,"BAT?",recon::dim);
}
} // namespace world
