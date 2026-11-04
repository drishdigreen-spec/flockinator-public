#pragma once
#include <cstring>
#include "console_model.h"

namespace flockinator {
// The driver packs two grayscale pixels per byte and outputs four-pixel groups.
inline Rect changed_region(const uint8_t* previous, const uint8_t* next) {
    int left=kWidth, top=kHeight, right=0, bottom=0;
    for(int y=0;y<kHeight;++y) {
        for(int x=0;x<kWidth/2;++x) {
            const int offset=y*kWidth/2+x;
            if(previous[offset]==next[offset]) continue;
            if(x*2<left) left=x*2;
            if(x*2+2>right) right=x*2+2;
            if(y<top) top=y;
            bottom=y+1;
        }
    }
    if(right==0) return {0,0,0,0};
    left&=~3; right=(right+3)&~3;
    return {left,top,right-left,bottom-top};
}

// The vendor expects a tightly packed region, not a pointer into a full-width row.
inline void pack_region(const uint8_t* pixels, Rect region, uint8_t* packed) {
    for(int y=0;y<region.h;++y)
        std::memcpy(packed+y*region.w/2,
                    pixels+(region.y+y)*kWidth/2+region.x/2,region.w/2);
}

inline bool require_full_refresh(bool has_frame, Page previous, Page next,
                                 bool explicit_refresh, bool sleeping) {
    return !has_frame || previous!=next || explicit_refresh || sleeping;
}
}
