"""Speaker mounting fit gauges. Execute with FreeCAD's bundled Python."""
import sys
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
import MeshPart
import json
from pathlib import Path
root=Path(__file__).resolve().parent
(root/'stl').mkdir(exist_ok=True)
d=A.newDocument('SpeakerFitGuides')
records=[]
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,A.Vector(x,y,z))
def cylinder(x,y,z,r,h):return Part.makeCylinder(r,h,A.Vector(x,y,z))
def export(name,s,kind,parameter):
    assert s.isValid() and len(s.Solids)==1
    assert abs(s.BoundBox.ZMin)<1e-6
    o=d.addObject('Part::Feature',name);o.Shape=s
    o.addProperty('App::PropertyString','Purpose');o.Purpose=kind
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,AngularDeflection=.15,Relative=False)
    mesh.write(str(root/'stl'/f'{name}.stl'))
    records.append({'file':name+'.stl','purpose':kind,'parameter_mm':parameter,'bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength],'volume_mm3':s.Volume})
    return o
# Open rails: 90 x 36 hole-centre pattern; 15 mm shoulder datum lets the
# speaker's approximately 9 mm rear projection clear the 3 mm base rails.
for diameter in [5.2,5.6,5.9]:
    shape=box(-50,-22,0,100,8,3).fuse(box(-50,14,0,100,8,3)).fuse(box(-4,-22,0,8,44,3))
    for x in [-45,45]:
        for y in [-18,18]:
            shape=shape.fuse(cylinder(x,y,2,4.5,13))
            # Small lead-in taper; no retaining barb: never force a speaker on.
            shape=shape.fuse(cylinder(x,y,15,diameter/2,4))
            shape=shape.fuse(Part.makeCone(diameter/2,diameter/2-.4,1,A.Vector(x,y,19)))
    shape=shape.removeSplitter()
    export('Speaker_post_guide_D'+str(diameter).replace('.','p'),shape,'Four posts, 90 x 36 pattern; shoulder height 15 mm',diameter)
# Open-ended C gauges: trial space between flat jaws, not flexible final clips.
for gap in [2.2,2.6,3.0]:
    shape=box(0,0,0,18,12,3).fuse(box(0,0,3,3,12,gap)).fuse(box(0,0,3+gap,18,12,3)).removeSplitter()
    export('Speaker_lug_gap_'+str(gap).replace('.','p'),shape,'Slide an accessible rigid lug edge between jaws; do not force',gap)
d.recompute()
d.saveAs(str(root/'Speaker-fit-guides.FCStd'))
(root/'manifest.json').write_text(json.dumps({'units':'mm','pattern_mm':[90,36],'parts':records,'status':'Fit gauges only; not installed mounts or final snap clips'},indent=2))
print('Exported six valid connected fit gauges, bed at Z=0.')
