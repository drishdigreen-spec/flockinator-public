#pragma once
#include "controller_json.h"
namespace board {
Json initial();
Json generate(uint32_t seed);
bool edit(Json& p,const Json& action,string& error);
Json simulate(const Json& p,int turns,Json* journals=nullptr,bool muted=false);
}
