#include "0510.h"
#include "0511.h"
#include "0512.h"
#include "0513.h"
#include "0514.h"
#include "0515.h"
#include "0515_3.h"
#include "0515_4.h"
#include "0518.h"
#include "0519_1.h"
#include "0520.h"
#include "0521.h"
#include "0522.h"
#include "0527.h"
#include "0528.h"
#include "0531.h"
#include "0601.h"
#include "0602.h"
#include "0628.h"
#include "0629.h"
#include "0629_2.h"
#include "0701.h"
#include "0707.h"
#include "0710.h"
#include "0712.h"
#include "0712_2.h"
#include "0713.h"
#include "0715.h"
#include "0716.h"
#include "0718.h"
#include "0719.h"
#include "a_big_hit.h"
#include "origin.h"
#include "wave_saw.h"
namespace patternflow_trial {
struct Pattern {const char* name;void(*setup)();void(*update)(float,const InputFrame&);void(*draw)();};
inline Pattern patterns[]={
{"0510",Pattern0510::setup,Pattern0510::update,Pattern0510::draw},
{"0511",Pattern0511::setup,Pattern0511::update,Pattern0511::draw},
{"0512",Pattern0512::setup,Pattern0512::update,Pattern0512::draw},
{"0513",Pattern0513::setup,Pattern0513::update,Pattern0513::draw},
{"0514",Pattern0514::setup,Pattern0514::update,Pattern0514::draw},
{"0515",Pattern0515::setup,Pattern0515::update,Pattern0515::draw},
{"0515-3",Pattern05153::setup,Pattern05153::update,Pattern05153::draw},
{"0515-4",Pattern05154::setup,Pattern05154::update,Pattern05154::draw},
{"0518",Pattern0518::setup,Pattern0518::update,Pattern0518::draw},
{"0519-1",Pattern05191::setup,Pattern05191::update,Pattern05191::draw},
{"0520",Pattern0520::setup,Pattern0520::update,Pattern0520::draw},
{"0521",Pattern0521::setup,Pattern0521::update,Pattern0521::draw},
{"0522",Pattern0522::setup,Pattern0522::update,Pattern0522::draw},
{"0527",Pattern0527::setup,Pattern0527::update,Pattern0527::draw},
{"0528",Pattern0528::setup,Pattern0528::update,Pattern0528::draw},
{"0531",Pattern0531::setup,Pattern0531::update,Pattern0531::draw},
{"0601",Pattern0601::setup,Pattern0601::update,Pattern0601::draw},
{"0602",Pattern0602::setup,Pattern0602::update,Pattern0602::draw},
{"Retro Digital Tapestry",RetroDigitalTapestry::setup,RetroDigitalTapestry::update,RetroDigitalTapestry::draw},
{"Chromatic Vortex",ChromaticAberrationVortexPattern::setup,ChromaticAberrationVortexPattern::update,ChromaticAberrationVortexPattern::draw},
{"Vector Field Flow",VectorFieldParticleFlowPattern::setup,VectorFieldParticleFlowPattern::update,VectorFieldParticleFlowPattern::draw},
{"Lissajous Weave",LissajousWeave::setup,LissajousWeave::update,LissajousWeave::draw},
{"Untitled pattern",UntitledPattern::setup,UntitledPattern::update,UntitledPattern::draw},
{"TileWaves",TileWaves::setup,TileWaves::update,TileWaves::draw},
{"Midsummer Sea",MidsummerSea::setup,MidsummerSea::update,MidsummerSea::draw},
{"Breakout Arcade",BreakoutArcade::setup,BreakoutArcade::update,BreakoutArcade::draw},
{"Firefly Hollow",FireflyHollow::setup,FireflyHollow::update,FireflyHollow::draw},
{"Poincaré Sphere",PoincareSphere::setup,PoincareSphere::update,PoincareSphere::draw},
{"Tri March",TriMarch::setup,TriMarch::update,TriMarch::draw},
{"Warped Wave",WarpedWave::setup,WarpedWave::update,WarpedWave::draw},
{"MagVortex",MagVortex::setup,MagVortex::update,MagVortex::draw},
{"a big hit",PatternABigHit::setup,PatternABigHit::update,PatternABigHit::draw},
{"Origin",Origin::setup,Origin::update,Origin::draw},
{"Wave Saw",WaveSaw::setup,WaveSaw::update,WaveSaw::draw},
};
inline constexpr unsigned count=sizeof(patterns)/sizeof(patterns[0]);
}
