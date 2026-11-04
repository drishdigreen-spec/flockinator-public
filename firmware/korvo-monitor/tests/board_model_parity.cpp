#include "board_model.h"
#include <cassert>
#include <iostream>
int main(){
  auto plan=board::initial();std::string error;
  assert(!board::edit(plan,Json{{"op",3}},error));
  assert(!board::edit(plan,Json::array(),error));
  assert(!board::edit(plan,Json{{"op","waypoint"},{"unit",0},{"pos",{-1,4}}},error));
  for(uint32_t seed=0;seed<100;seed++){
    auto p=board::generate(seed);
    std::cout<<board::simulate(p,46).dump()<<'\n';
  }
}
