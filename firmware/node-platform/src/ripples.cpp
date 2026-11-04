#include "ripples.h"
#ifdef FLOCK_PATTERNFLOW_TRIAL
#include "ripple_model.h"
#include "network.h"
#include "esp_random.h"
#include "esp_timer.h"
#include "lwip/sockets.h"
#include <fcntl.h>
#include <unistd.h>
namespace {
constexpr uint16_t Port=49170;
const char* const addresses[16]={
"192.168.1.10","192.168.1.10","192.168.1.10","192.168.1.10",
"192.168.1.10","192.168.1.10","192.168.1.10","192.168.1.10",
"192.168.1.10","192.168.1.10","192.168.1.10","192.168.1.10",
"192.168.1.10","192.168.1.10","192.168.1.10","192.168.1.10",
};
int fd=-1,own=-1;
uint32_t boot=0,sequence=0,next_at=0,retry_at=0;
uint32_t sent=0,received=0,confirmed=0,duplicates=0,rejected=0,send_errors=0,ack_timeouts=0,event_overwrites=0,socket_errors=0;
ripple::Seen seen[16];ripple::Pending pending;
ripple::Event events[8];unsigned event_next=0;
char last_from[3]="--",last_to[3]="--",last_ack_from[3]="--";
uint32_t received_sequence=0,ack_sequence=0;
uint32_t last_rx=0,last_ack=0,last_rtt=0,peer_rx[16]{};
void label_of(int index,char out[3]){out[0]='A'+index%4;out[1]='1'+index/4;out[2]=0;}
void event(int peer,ripple::EventKind kind,uint32_t now){
 auto& e=events[event_next++%8];if(e.active&&uint32_t(now-e.at)<ripple::Lifetime)event_overwrites++;
 e={true,uint8_t(peer),kind,now};
}
bool send_packet(const ripple::Packet& p){
 sockaddr_in target{};target.sin_family=AF_INET;target.sin_port=htons(Port);inet_pton(AF_INET,addresses[p.to],&target.sin_addr);
 uint8_t bytes[16];ripple::encode(p,bytes);
 if(sendto(fd,bytes,sizeof(bytes),0,reinterpret_cast<sockaddr*>(&target),sizeof(target))!=sizeof(bytes)){send_errors++;return false;}return true;
}
}
void ripples_tick(const char* label){
 uint32_t now=uint32_t(esp_timer_get_time()/1000);
 int index=ripple::index(label);if(index<0||!network_connected())return;
 if(own!=index){own=index;boot=esp_random();if(!boot)boot=1;sequence=0;pending={};for(auto& s:seen)s={};next_at=now+1500+esp_random()%3000;}
 if(fd<0){
  if(retry_at&&int32_t(now-retry_at)<0)return;
  fd=socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP);
  sockaddr_in local{};local.sin_family=AF_INET;local.sin_port=htons(Port);local.sin_addr.s_addr=htonl(INADDR_ANY);
  if(fd<0||fcntl(fd,F_SETFL,O_NONBLOCK)<0||bind(fd,reinterpret_cast<sockaddr*>(&local),sizeof(local))<0){if(fd>=0)close(fd);fd=-1;socket_errors++;retry_at=now+5000;return;}
 }
 if(pending.active&&uint32_t(now-pending.at)>=ripple::AckDeadline){pending.active=false;ack_timeouts++;}
 for(unsigned work=0;work<8;work++){
  uint8_t bytes[17];sockaddr_in source{};socklen_t length=sizeof(source);
  int n=recvfrom(fd,bytes,sizeof(bytes),0,reinterpret_cast<sockaddr*>(&source),&length);if(n<0)break;
  ripple::Packet p{};
  if(!ripple::decode(bytes,size_t(n),p)||p.to!=own||source.sin_port!=htons(Port)){rejected++;continue;}
  in_addr expected{};inet_pton(AF_INET,addresses[p.from],&expected);
  if(source.sin_addr.s_addr!=expected.s_addr){rejected++;continue;}
  if(p.kind==1){
   if(peer_rx[p.from]&&uint32_t(now-peer_rx[p.from])<100){rejected++;continue;}
   if(seen[p.from].accept(p.boot,p.sequence)){received++;received_sequence=p.sequence;peer_rx[p.from]=now;last_rx=now;label_of(p.from,last_from);event(p.from,ripple::EventKind::Arrival,now);}
   else {duplicates++;continue;}
   send_packet({2,uint8_t(own),p.from,p.boot,p.sequence});
  }else if(pending.matches(p,now)){
   pending.active=false;confirmed++;ack_sequence=p.sequence;label_of(p.from,last_ack_from);last_ack=now;last_rtt=now-pending.at;event(p.from,ripple::EventKind::Confirmed,now);
  }else rejected++;
 }
 if(int32_t(now-next_at)<0||pending.active)return;
 next_at=now+3500+esp_random()%3001;
 uint8_t peers[4];unsigned count=0;for(int i=0;i<16;i++)if(ripple::neighbour(own,i))peers[count++]=i;
 if(!count)return;uint8_t target=peers[esp_random()%count];if(++sequence==0)sequence=1;
 if(send_packet({1,uint8_t(own),target,boot,sequence})){
  sent++;pending.start(target,boot,sequence,now);label_of(target,last_to);event(target,ripple::EventKind::Departure,now);
 }
}
void ripples_draw(node::Frame& frame,uint32_t now){if(own<0)return;for(const auto& e:events)ripple::draw(frame,e,own,now);}
void ripples_json(cJSON* root){
 auto* j=cJSON_AddObjectToObject(root,"ripples");
 cJSON_AddStringToObject(j,"transport","experimental UDP; roster checked, not authenticated");
 cJSON_AddStringToObject(j,"purpose","generated neighbour pulse messages; not management telemetry");
 cJSON_AddStringToObject(j,"layout","A-D left-to-right, 1-4 top-to-bottom");
 cJSON_AddBoolToObject(j,"ready",fd>=0&&network_connected());
 cJSON_AddNumberToObject(j,"port",Port);cJSON_AddNumberToObject(j,"sent",sent);cJSON_AddNumberToObject(j,"received",received);cJSON_AddNumberToObject(j,"acknowledged",confirmed);
 cJSON_AddNumberToObject(j,"ack_timeouts",ack_timeouts);cJSON_AddNumberToObject(j,"duplicates",duplicates);cJSON_AddNumberToObject(j,"rejected",rejected);cJSON_AddNumberToObject(j,"send_errors",send_errors);cJSON_AddNumberToObject(j,"socket_errors",socket_errors);cJSON_AddNumberToObject(j,"event_overwrites",event_overwrites);
 cJSON_AddNumberToObject(j,"last_sent_sequence",sequence);cJSON_AddNumberToObject(j,"last_received_sequence",received_sequence);cJSON_AddNumberToObject(j,"last_acknowledged_sequence",ack_sequence);
 cJSON_AddStringToObject(j,"last_ack_from",last_ack_from);
 cJSON_AddStringToObject(j,"last_from",last_from);cJSON_AddStringToObject(j,"last_to",last_to);
 cJSON_AddNumberToObject(j,"last_received_ms",last_rx);cJSON_AddNumberToObject(j,"last_acknowledged_ms",last_ack);cJSON_AddNumberToObject(j,"last_rtt_ms",last_rtt);
}
#else
void ripples_tick(const char*){}
void ripples_draw(node::Frame&,uint32_t){}
void ripples_json(cJSON*){}
#endif
