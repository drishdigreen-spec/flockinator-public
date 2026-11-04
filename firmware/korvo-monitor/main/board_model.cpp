#include "board_model.h"
#include "lab_model.h"
extern "C" {
#include "vendor/blake2.h"
}
#include <set>
#include <array>
#include <algorithm>
#include <cmath>
namespace board {
using Tile=std::array<int,2>;
constexpr Tile home={7,11};
constexpr int reserve=3;
const char* patterns[]={"Tree-line fan","Search grid"};
const char* covers[]={"Open","Patchy","Dense"};
const char* kinds[]={"Enemy","Friendly"};
const int packs[]={16,30,44}, fleets[]={4,8,16};
bool tile(const Json& v){return v.is_array()&&v.size()==2&&natural(v[0],15)&&natural(v[1],11);}
int distance(Tile a,Tile b){return std::max(abs(a[0]-b[0]),abs(a[1]-b[1]));}
Tile step(Tile a,Tile b){for(int j=0;j<2;j++)a[j]+=(b[j]>a[j])-(b[j]<a[j]);return a;}
Json initial(){return {{"revision",0u},{"pattern",patterns[0]},{"cover",covers[1]},{"count",8},{"battery",30},{"focus",{7,3}},{"contacts",Json::array()},{"custom",Json::object()},{"seed",1u},{"phase","Draft"},{"turn",0},{"since",nullptr}};}
Json generate(uint32_t seed){
    signals::Rng r;r.array_seed(&seed,1);Json p=initial();
    p["scenario_seed"]=p["seed"]=seed;p["battery"]=packs[r.below(3)];
    p["pattern"]=patterns[r.below(2)];p["cover"]=covers[r.below(3)];p["count"]=fleets[r.below(3)];
    p["focus"]={r.below(16),1+r.below(9)};
    const int low[]={0,1,4,11},high[]={0,3,10,24};int band=r.below(4),n=low[band]+r.below(high[band]-low[band]+1);
    std::vector<Tile> pool,chosen;for(int x=0;x<16;x++)for(int y=0;y<12;y++)if(Tile{x,y}!=home)pool.push_back({x,y});
    // Both sample strategies used by the desktop's random.Random.sample.
    int threshold=21;if(n>5){int k=4;while(k<n*3)k*=4;threshold+=k;}
    std::set<int> used;
    for(int i=0;i<n;i++){
        if(int(pool.size())<=threshold){int j=r.below(int(pool.size())-i);chosen.push_back(pool[j]);pool[j]=pool[pool.size()-i-1];}
        else{int j;do{j=r.below(pool.size());}while(!used.insert(j).second);chosen.push_back(pool[j]);}
    }
    for(auto pos:chosen)p["contacts"].push_back({{"pos",pos},{"kind",kinds[r.below(2)]},{"priority",r.below(3)==2?"High":"Normal"},{"outcome","Unassessed"}});
    return p;
}
bool edit(Json& p,const Json& a,string& err){
    if(!a.is_object()||!a.contains("op")||!a["op"].is_string()){err="Invalid planner edit";return false;}
    auto op=a.value("op",string{});Json pos=a.contains("pos")?a["pos"]:Json(nullptr);
    if(op=="setting"&&a.contains("key")&&a["key"].is_string()&&a.contains("value")){
        string k=a["key"];auto v=a["value"];
        if((k=="count"&&(v==4||v==8||v==16))||(k=="battery"&&(v==16||v==30||v==44))||
           (k=="pattern"&&(v==patterns[0]||v==patterns[1]))||(k=="cover"&&(v==covers[0]||v==covers[1]||v==covers[2]))){p[k]=v;return true;}
    }else if(op=="focus"&&tile(pos)){p["focus"]=pos;return true;}
    else if((op=="erase"||op=="contact")&&tile(pos)){
        auto& contacts=p["contacts"];
        auto it=std::find_if(contacts.begin(),contacts.end(),[&](const Json& c){return c["pos"]==pos;});
        if(op=="erase"){if(it!=contacts.end())contacts.erase(it);return true;}
        if(a.contains("kind")&&(a["kind"]=="Enemy"||a["kind"]=="Friendly")&&a.contains("priority")&&(a["priority"]=="Normal"||a["priority"]=="High")){
            Json c={{"pos",pos},{"kind",a["kind"]},{"priority",a["priority"]},{"outcome","Unassessed"}};
            if(it!=contacts.end())*it=c;else if(contacts.size()<24)contacts.push_back(c);else{err="Contact limit reached";return false;}return true;
        }
    }else if((op=="undo"||op=="preset"||op=="waypoint")&&a.contains("unit")&&natural(a["unit"],p["count"].get<int>()-1)){
        string k=std::to_string(a["unit"].get<int>());auto& custom=p["custom"];
        if(op=="waypoint"){if(!tile(pos)||custom[k].size()>=16){err="Invalid waypoint or route full";return false;}custom[k].push_back(pos);}
        else if(op=="undo"&&custom.contains(k)&&custom[k].size()>1)custom[k].erase(custom[k].size()-1);else custom.erase(k);
        return true;
    }else if(op=="reroll"){p["seed"]=p["seed"].get<uint32_t>()+1u;return true;}
    err="Invalid planner edit";return false;
}
static int draw(uint32_t seed,Tile pos,int unit,const char* purpose){
    char buf[96];int n=snprintf(buf,sizeof(buf),"%lu/(%d, %d)/%d/%s",(unsigned long)seed,pos[0],pos[1],unit,purpose);
    uint8_t b[4];blake2s(b,4,buf,n,nullptr,0);
    return ((uint32_t(b[0])<<24)|(uint32_t(b[1])<<16)|(uint32_t(b[2])<<8)|b[3])%100;
}
struct Unit{Tile pos=home;int energy=0,next=0,verify=-1,planned=0;string role="Search",reason;std::vector<Tile> path;};
Json simulate(const Json& p,int turns,Json* journals,bool muted){
    const int count=p["count"],battery=p["battery"];const Tile focus=p["focus"];const auto& contacts=p["contacts"];
    const uint32_t seed=p["seed"];
    std::vector<Unit> units(count);std::vector<Json> reports(contacts.size(),Json::array());
    std::set<Tile> seen;bool tried[16][24]{},assigned[24]{};Json checks=Json::array(),outside=Json::array();
    const int cover=p["cover"]=="Open"?0:p["cover"]=="Patchy"?1:2;
    int detect[]={85,65,45},acc[]={82,70,60};
    auto record=[&](int i,int tick,const char* event,Json details){
        if(journals){details["unit"]=unit_label(i);details["turn"]=tick;details["event"]=event;(*journals)[i].push_back(std::move(details));}
    };
    for(int i=0;i<count;i++){
        auto& u=units[i];u.energy=battery;string key=std::to_string(i);
        if(p["custom"].contains(key))u.path=p["custom"][key].get<std::vector<Tile>>();
        else if(p["pattern"]==patterns[0])u.path.push_back({std::clamp(focus[0]-count/2,0,16-count)+i,focus[1]});
        else for(int k=i*32/count;k<(i+1)*32/count;k++)u.path.push_back({std::clamp(focus[0]-4,0,8)+(k/8%2?7-k%8:k%8),std::clamp(focus[1]-2,0,8)+k/8});
        Tile prev=home;for(auto t:u.path){u.planned+=distance(prev,t);prev=t;}u.planned+=distance(prev,home);
        if(journals)record(i,0,"route_assigned",{{"tile",home},{"energy",battery},{"reserve",reserve},{"route",u.path}});
    }
    int tick=0;
    while(tick<turns && !std::all_of(units.begin(),units.end(),[](auto& u){return u.role=="Home";})){
        ++tick;
        for(int i=0;i<count;i++){
            auto& u=units[i];if(u.role=="Home")continue;
            if(u.verify>=0 && tried[i][u.verify])u.verify=-1;
            if(u.role!="Return" && u.verify<0){
                while(u.next<int(u.path.size())&&u.path[u.next]==u.pos)u.next++;
                if(u.next==int(u.path.size())){u.role="Return";u.reason="Route complete";}
                else if(u.energy-1<distance(step(u.pos,u.path[u.next]),home)+reserve){u.role="Return";u.reason="Return reserve";}
            }
            Tile target=u.verify>=0?contacts[u.verify]["pos"].get<Tile>():u.role=="Return"?home:u.path[u.next];
            if(journals&&u.role=="Return"&&u.pos!=home)record(i,tick,"return_step",{{"tile",u.pos},{"energy_before",u.energy},{"steps_home",distance(u.pos,home)},{"rule",u.reason}});
            if(u.pos!=target){u.pos=step(u.pos,target);--u.energy;}
            if(u.role=="Return"){if(u.pos==home){u.role="Home";if(journals)record(i,tick,"landed",{{"tile",home},{"energy",u.energy},{"rule",u.reason}});}continue;}
            int x=u.pos[0],y=u.pos[1],hits=0;std::vector<Tile> footprint;
            for(Tile t:{Tile{x-1,y},Tile{x,y-1},u.pos,Tile{x,y+1},Tile{x+1,y}})if(t[0]>=0&&t[0]<16&&t[1]>=0&&t[1]<12){seen.insert(t);footprint.push_back(t);}
            u.role=u.verify>=0?"Verify":"Search";
            for(int k=0;k<int(contacts.size());k++){
                const auto& c=contacts[k];Tile pos=c["pos"];
                if(tried[i][k]||abs(x-pos[0])+abs(y-pos[1])>1)continue;
                tried[i][k]=true;int band=abs(pos[1]-focus[1])<=1?cover:0;
                if(draw(seed,pos,i,"spot")>=detect[band])continue;
                string kind=c["kind"];if(draw(seed,pos,i,"identify")>=acc[band])kind=kind=="Friendly"?"Enemy":"Friendly";
                reports[k].push_back({{"unit",i},{"label",kind},{"turn",tick}});hits++;u.role="Observe";
                if(journals)record(i,tick,"discovery",{{"tile",pos},{"contact",k+1},{"reported_label",kind},{"rule","first_independent_sighting"}});
            }
            if(journals)record(i,tick,"scan",{{"tile",u.pos},{"energy",u.energy},{"next_tile",target},{"footprint",footprint},{"signals",hits},{"role",u.role}});
        }
        for(int k=0;k<int(contacts.size());k++){
            if(assigned[k]||reports[k].size()!=1||contacts[k]["priority"]!="High")continue;
            Tile pos=contacts[k]["pos"];int best=-1,dist=1000;
            for(int i=0;i<count;i++){auto& u=units[i];int d=distance(u.pos,pos);
                if((u.role=="Observe"||u.role=="Search")&&u.verify<0&&!tried[i][k]&&d+distance(pos,home)+reserve<=u.energy&&d<dist){best=i;dist=d;}}
            if(best<0)continue;
            assigned[k]=true;int src=reports[k][0]["unit"];
            if(journals){Json pkt={{"contact",k+1},{"message",std::to_string(tick)+"-"+std::to_string(k+1)},{"sender",unit_label(src)},{"recipient",unit_label(best)},{"transport","simulated_planner_relay"},{"content","request_independent_check"}};
                record(src,tick,"message_sent",pkt);record(muted?src:best,tick,muted?"message_withheld":"message_received",pkt);}
            if(muted)continue;
            units[best].verify=k;checks.push_back({{"contact",k},{"unit",best},{"turn",tick}});
            if(journals)record(best,tick,"check_assigned",{{"rule","high_priority_single_report_with_return_budget"},{"energy",units[best].energy},{"tile",units[best].pos},{"destination",pos}});
        }
    }
    Json nodes=Json::array(),paths=Json::array();bool complete=true;
    for(auto& u:units){paths.push_back(u.path);nodes.push_back({{"pos",u.pos},{"energy",u.energy},{"role",u.role},{"reason",u.reason},{"planned",u.planned},{"waypoint",u.next},{"verify",u.verify<0?Json(nullptr):Json(u.verify)}});complete&=u.role=="Home";}
    for(int k=0;k<int(contacts.size());k++)if(2*distance(home,contacts[k]["pos"])+reserve>battery)outside.push_back(k);
    return {{"plan",p},{"sim",{{"turn",tick},{"units",nodes},{"paths",paths},{"seen",seen},{"reports",reports},{"checks",checks}}},
            {"phase",complete?Json("Complete"):p["phase"]},{"odds",{detect[cover],acc[cover]}},{"beyond_return",outside}};
}
}
