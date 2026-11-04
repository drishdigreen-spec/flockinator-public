#pragma once
#include <cstdint>
#include <algorithm>
namespace node {
inline uint16_t glyph(char c) {
    switch(c) {
        case '0': return 0x7b6f;
        case '1': return 0x2c97;
        case '2': return 0x73e7;
        case '3': return 0x73cf;
        case '4': return 0x5bc9;
        case '5': return 0x79cf;
        case '6': return 0x79ef;
        case '7': return 0x7292;
        case '8': return 0x7bef;
        case '9': return 0x7bcf;
        case 'A': return 0x2bed;
        case 'B': return 0x6bae;
        case 'C': return 0x7927;
        case 'D': return 0x6b6e;
        case 'E': return 0x79a7;
        case 'F': return 0x79a4;
        case 'G': return 0x796f;
        case 'H': return 0x5bed;
        case 'I': return 0x7497;
        case 'J': return 0x126f;
        case 'K': return 0x5bad;
        case 'L': return 0x4927;
        case 'M': return 0x5fed;
        case 'N': return 0x5ffd;
        case 'O': return 0x7b6f;
        case 'P': return 0x7be4;
        case 'Q': return 0x7b79;
        case 'R': return 0x6bad;
        case 'S': return 0x79cf;
        case 'T': return 0x7492;
        case 'U': return 0x5b6f;
        case 'V': return 0x5b6a;
        case 'W': return 0x5bfd;
        case 'X': return 0x5aad;
        case 'Y': return 0x5a92;
        case 'Z': return 0x72a7;
        case '-': return 0x01c0;
        case '.': return 0x0002;
        case ':': return 0x0410;
        case '/': return 0x12a4;
        case '?': return 0x72c2;
        case '%': return 0x52a5;
        default: return 0;
    }
}
struct Frame {
    uint16_t pixels[64*64]{};
    bool clipped=false;
    void clear(uint16_t color=0) { std::fill(pixels,pixels+4096,color); clipped=false; }
    void pixel(int x,int y,uint16_t color) {
        if(x<0 || x>=64 || y<0 || y>=64) { clipped=true; return; }
        pixels[y*64+x]=color;
    }
    void text(int x,int y,const char* s,int scale,uint16_t color) {
        for(;*s;s++,x+=4*scale) {
            uint16_t bits=glyph(*s);
            for(int row=0;row<5;row++) for(int col=0;col<3;col++)
                if(bits & (1<<(14-row*3-col)))
                    for(int a=0;a<scale;a++) for(int b=0;b<scale;b++) pixel(x+col*scale+a,y+row*scale+b,color);
        }
    }
};
inline void dashboard(Frame& f,const char* label,const char* title,const char* const lines[5]) {
    f.clear(); f.text(3,2,label,3,0xffff); f.text(30,6,"TEST",1,0x07ff);
    f.text(2,21,title,1,0x07ff);
    for(int i=0;i<5;i++) f.text(2,29+7*i,lines[i],1,0xffff);
}
}
