#pragma once
#include "survey_render.h"
#include "cJSON.h"
#include <cstring>
namespace survey {
inline bool integer(cJSON* v,double lo,double hi){return cJSON_IsNumber(v)&&std::isfinite(v->valuedouble)&&v->valuedouble>=lo&&v->valuedouble<=hi&&std::floor(v->valuedouble)==v->valuedouble;}
inline bool parse(cJSON* root,Packet& p){
 if(!cJSON_IsObject(root)||cJSON_GetArraySize(root)!=12)return false;
 for(auto* v=root->child;v;v=v->next){
  if(!v->string)return false;
  for(auto* prior=root->child;prior!=v;prior=prior->next)if(!strcmp(v->string,prior->string))return false;
  bool allowed=false;for(const char* key:{"op","run","seq","t","n","p","e","d","s","r","q","v"})if(!strcmp(key,v->string))allowed=true;if(!allowed)return false;
 }
 auto get=[&](const char* name){return cJSON_GetObjectItemCaseSensitive(root,name);};
 if(!integer(get("v"),2,2))return false;
 for(const char* key:{"run","seq","t"})if(!integer(get(key),!strcmp(key,"t")?0:1,UINT32_MAX))return false;
 if(!integer(get("n"),0,15)||!integer(get("e"),0,10000)||!integer(get("d"),-1,99999)||!integer(get("s"),0,7)||!integer(get("r"),0,2))return false;
 auto* pose=get("p");if(!cJSON_IsArray(pose)||cJSON_GetArraySize(pose)!=6)return false;
 float a[6];for(int i=0;i<6;i++){auto* value=cJSON_GetArrayItem(pose,i);if(!integer(value,-100000,100000))return false;a[i]=value->valuedouble/10;}
 p.run=get("run")->valuedouble;p.seq=get("seq")->valuedouble;p.time=get("t")->valuedouble;p.node=get("n")->valueint;p.energy=get("e")->valueint;p.distance=get("d")->valueint;p.state=get("s")->valueint;p.reserve=get("r")->valueint;p.pose={{a[0],a[1],a[2]},a[3],a[4],a[5]};
 auto* peers=get("q");if(!cJSON_IsArray(peers)||cJSON_GetArraySize(peers)>3)return false;
 p.peerCount=cJSON_GetArraySize(peers);
 for(int i=0;i<p.peerCount;i++){auto* peer=cJSON_GetArrayItem(peers,i);if(!cJSON_IsArray(peer)||cJSON_GetArraySize(peer)!=4)return false;for(int j=0;j<4;j++)if(!integer(cJSON_GetArrayItem(peer,j),j? -100000:0,j?100000:15))return false;p.peers[i]={cJSON_GetArrayItem(peer,0)->valueint,{float(cJSON_GetArrayItem(peer,1)->valuedouble/10),float(cJSON_GetArrayItem(peer,2)->valuedouble/10),float(cJSON_GetArrayItem(peer,3)->valuedouble/10)}};}
 return true;
}
}
