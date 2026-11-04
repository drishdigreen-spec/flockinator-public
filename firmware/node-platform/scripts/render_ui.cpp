#include "pixel_ui.h"
#include <fstream>
int main(int argc,char** argv) {
    if(argc!=2) return 2;
    node::Frame f; const char* lines[]={"RAM PASS","SHT PASS","IMU PASS","VISUAL PENDING","PRESS BOOT NEXT"};
    node::dashboard(f,"A1","OVERVIEW",lines);
    if(f.clipped) return 1;
    std::ofstream out(argv[1],std::ios::binary); out<<"P6\n64 64\n255\n";
    for(auto pixel:f.pixels) { char rgb[]={static_cast<char>(((pixel>>11)&31)*255/31),static_cast<char>(((pixel>>5)&63)*255/63),static_cast<char>((pixel&31)*255/31)}; out.write(rgb,3); }
    return !out.good();
}
