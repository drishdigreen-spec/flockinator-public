#include "lab_model.h"
#include <cstdio>
#include <cstring>
#include <algorithm>
namespace signals {
// Match the desktop lab's Random(string), including its MT19937 array seed.
// This keeps previously recorded exercise seeds comparable on the controller.
bool Rng::seed(uint32_t value,const char* phase,Hash hash){
    unsigned char bytes[128]{};
    int n=snprintf(reinterpret_cast<char*>(bytes),64,"field-signals-v1/%lu/%s",(unsigned long)value,phase);
    if(n<0 || n>=64 || !hash(reinterpret_cast<char*>(bytes),bytes+n)) return false;
    n+=64;uint32_t key[32]{};
    for(int j=0;j<n;j++)key[j/4]|=uint32_t(bytes[n-1-j])<<(8*(j%4));
    const int length=(n+3)/4;
    array_seed(key,length);return true;
}
void Rng::array_seed(const uint32_t* key,int length){
    words[0]=19650218u;
    for(unsigned i=1;i<624;i++)words[i]=1812433253u*(words[i-1]^(words[i-1]>>30))+i;
    int i=1,j=0;
    for(int k=0;k<624;k++){
        words[i]=(words[i]^((words[i-1]^(words[i-1]>>30))*1664525u))+key[j]+j;
        if(++i==624){words[0]=words[623];i=1;}
        if(++j==length)j=0;
    }
    for(int k=0;k<623;k++){
        words[i]=(words[i]^((words[i-1]^(words[i-1]>>30))*1566083941u))-i;
        if(++i==624){words[0]=words[623];i=1;}
    }
    words[0]=0x80000000u;cursor=624;
}
uint32_t Rng::next(){
    if(cursor==624){
        for(int i=0;i<624;i++){
            uint32_t v=(words[i]&0x80000000u)|(words[(i+1)%624]&0x7fffffffu);
            words[i]=words[(i+397)%624]^(v>>1)^((v&1)?0x9908b0dfu:0);
        }
        cursor=0;
    }
    uint32_t v=words[cursor++];v^=v>>11;v^=(v<<7)&0x9d2c5680u;v^=(v<<15)&0xefc60000u;
    return v^(v>>18);
}
int Rng::below(int n){int bits=0;for(int m=n;m;m>>=1)bits++;int x;do{x=next()>>(32-bits);}while(x>=n);return x;}
double Rng::fraction(){uint32_t a=next()>>5,b=next()>>6;return (a*67108864.0+b)/9007199254740992.0;}
static void generate(Rng& rng,World& w){
    for(auto& t:w.truth)t=rng.below(3);
    for(int i=0;i<Units;i++){
        int t=w.truth[i/4];w.cue[i]=rng.fraction()<.65?t:(t+1+rng.below(2))%3;
    }
    for(int j=0;j<48;j++){w.lost[j]=rng.fraction()<.5;w.replacement[j]=rng.below(3);}
}
static int peer(int receiver,int slot){return (receiver/4)*4+slot+(slot>=receiver%4);}
static int symbol(const Model& m,const World& w,int i,int j,Link link){
    int k=i*3+j,s=peer(i,j);
    if(link==Muted || (link==HalfLost && w.lost[k]))return 3;
    return link==Scrambled?w.replacement[k]:m.book[s][w.cue[s]];
}
static int meaning(const uint8_t* counts){
    int winner=int(std::max_element(counts,counts+3)-counts);
    return counts[0]+counts[1]+counts[2]>=3 && std::count(counts,counts+3,counts[winner])==1?winner:3;
}
bool Model::init(uint32_t seed,Link link,Hash hash){
    turn=0;intervention=link;
    std::fill_n(scores,4,Score{});solo={};
    std::fill_n(memory,2,Memory{});std::fill_n(training_packets,2,0);
    std::fill_n(known,2,0);std::fill_n(mappings,2,0);
    if(!training.seed(seed,"codebooks",hash))return false;
    for(auto& b:book){int pool[]={0,1,2};for(int j=0;j<3;j++){int n=training.below(3-j);b[j]=pool[n];pool[n]=pool[2-j];}}
    return training.seed(seed,"train",hash)&&testing.seed(seed,"test",hash);
}
Choice Model::choose(const World& w,int i,int arm,Link link) const{
    Choice c{};int votes[3]{};votes[w.cue[i]]=1;
    for(int j=0;j<3;j++){
        int token=symbol(*this,w,i,j,link);c.token[j]=token;
        c.decoded[j]=token==3?3:meaning(memory[arm].counts[i][j][token]);
        if(c.decoded[j]!=3)votes[c.decoded[j]]++;
    }
    int most=int(std::max_element(votes,votes+3)-votes);
    c.sector=votes[w.cue[i]]==votes[most]?w.cue[i]:most;return c;
}
void Model::step(){
    if(turn>=Train+Test)return;
    if(turn<Train){
        World w;generate(training,w);
        for(int a=0;a<2;a++)for(int i=0;i<Units;i++)for(int j=0;j<3;j++){
            int t=symbol(*this,w,i,j,a?intervention:Clear);
            if(t<3){memory[a].counts[i][j][t][w.truth[i/4]]++;training_packets[a]++;}
        }
        if(turn+1==Train){
            for(int a=0;a<2;a++)for(int i=0;i<Units;i++)for(int j=0;j<3;j++)for(int t=0;t<3;t++){
                int decoded=meaning(memory[a].counts[i][j][t]);
                if(decoded<3){known[a]++;mappings[a]+=book[peer(i,j)][decoded]==t;}
            }
        }
    }else{
        World& w=held[turn-Train];generate(testing,w);
        for(int a=0;a<5;a++){
            Score& s=a==4?solo:scores[a];int team_hits[4]{};
            for(int i=0;i<Units;i++){
                auto c=choose(w,i,a<4?a/2:0,a==4?Muted:(a%2?intervention:Clear));
                for(auto t:c.token)s.packets+=t<3;
                if(c.sector==w.truth[i/4]){s.correct++;team_hits[i/4]++;}
            }
            for(int h:team_hits)s.recovered+=h>=3;
        }
    }
    turn++;
}
}
