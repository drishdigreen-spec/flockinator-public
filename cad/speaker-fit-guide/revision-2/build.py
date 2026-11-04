"""Revised fit gauges from owner feedback, 28 October 2026. FreeCAD runtime."""
import sys
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part, MeshPart
from pathlib import Path
import json
root=Path(__file__).resolve().parent
(root/'stl').mkdir(exist_ok=True)
d=A.newDocument('SpeakerFitGuidesV2')
records=[]
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,A.Vector(x,y,z))
def cylinder(x,y,z,r,h):return Part.makeCylinder(r,h,A.Vector(x,y,z))
def save(name,shape,parameters):
    assert shape.isValid() and len(shape.Solids)==1 and abs(shape.BoundBox.ZMin)<1e-6
    o=d.addObject('Part::Feature',name);o.Shape=shape
    MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.15,Relative=False).write(str(root/'stl'/(name+'.stl')))
    records.append(dict(file=name+'.stl',**parameters))
# Same rails, width, shoulder height and posts; only lengthwise centres change.
s=box(-51,-22,0,102,8,3).fuse(box(-51,14,0,102,8,3)).fuse(box(-4,-22,0,8,44,3))
for x in [-46,46]:
    for y in [-18,18]:
        s=s.fuse(cylinder(x,y,2,4.5,13)).fuse(cylinder(x,y,15,2.8,4))
        s=s.fuse(Part.makeCone(2.8,2.4,1,A.Vector(x,y,19)))
save('Speaker_post_guide_92x36_D5p6_v2',s.removeSplitter(),{'pattern_mm':[92,36],'post_diameter_mm':5.6,'shoulder_height_mm':15})
# Side-oriented exports eliminate the jaw overhang; import without rotation.
for gap in [2.0,2.1,2.2]:
    s=box(0,0,0,18,12,3).fuse(box(0,0,3,3,12,gap)).fuse(box(0,0,3+gap,18,12,3)).removeSplitter()
    s.rotate(A.Vector(0,0,0),A.Vector(1,0,0),90)
    s.translate(A.Vector(0,-s.BoundBox.YMin,-s.BoundBox.ZMin))
    save('Speaker_lug_gap_'+str(gap).replace('.','p')+'_v2',s,{'gap_mm':gap,'orientation':'Already on broad side; no further rotation needed'})
d.recompute();d.saveAs(str(root/'Speaker-fit-guides-v2.FCStd'))
(root/'manifest.json').write_text(json.dumps({'units':'mm','speaker_body_owner_mm':[99.6,44.5,21],'speaker_lug_owner_mm':1.9,'parts':records,'status':'Experimental fit gauges, not installed retention'},indent=2))
print('Four revision-2 gauges exported; shapes valid, one solid each.')
