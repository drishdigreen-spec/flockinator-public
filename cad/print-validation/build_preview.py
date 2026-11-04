"""Local-only CAD mock-up, not a plate to print as one object. FreeCAD bundled runtime."""
import sys,math,json
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part,Mesh
r=Path(__file__).resolve().parent;doc=App.newDocument('FlockinatorOpticalValidation')
def feature(name,shape):
 o=doc.addObject('Part::Feature',name);o.Shape=shape;return o
panel=feature('Panel160mm_reference_only',Part.makeBox(160,160,6,App.Vector(20,20,-6)))
panel.addProperty('App::PropertyString','Note');panel.Note='Panel depth and LED Z unmeasured; reference only, do not print'
for name,path,z in [('BlackGrid3mm','stl/Flockinator_64x64_P2p5_wall0p4_depth3_mm.stl',2),('WhiteSheet03mm','stl/Flockinator_full_panel_diffusion_sheet_0p3_mm.stl',5)]:
 o=doc.addObject('Mesh::Feature',name);o.Mesh=Mesh.Mesh(str(r/path));o.Placement.Base=App.Vector(20,20,z)
 o.addProperty('App::PropertyString','Note');o.Note='2 mm gap above reference panel face is provisional; set from measured LED package height'
base=r/'purchased-original-samples'
def stock(name,file,angle,cx,cy,ox,oy):
 m=Mesh.Mesh(str(base/file));a=math.radians(angle);c=math.cos(a);s=math.sin(a);t=App.Matrix()
 t.A11=c;t.A12=0;t.A13=-s;t.A21=s;t.A22=0;t.A23=c;t.A31=0;t.A32=1;t.A33=0
 t.A14=ox-c*cx+s*cy;t.A24=oy-s*cx-c*cy;t.A34=-18
 m.transform(t);m.flipNormals();o=doc.addObject('Mesh::Feature',name);o.Mesh=m
for prefix,file in [('CornerTrack','track_90_150.stl'),('CornerSkin','skin_mattehex_90_150_lh.stl')]:stock(prefix,file,-90,0,50,0,0)
for prefix,file in [('Track','track_straight_100.stl'),('Skin','skin_mattehex_straight_100.stl')]:
 stock(prefix+'Horizontal',file,-90,0,25,75,0);stock(prefix+'Vertical',file,0,0,25,0,75)
doc.recompute();doc.saveAs(str(r/'Flockinator-optical-test-layout.FCStd'))
print('SAVED optical test layout: full64x64 + source corner and two stock100mm legs; not complete closed border')
