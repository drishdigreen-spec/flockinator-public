"""FreeCAD bundled Python, no GUI launch. GPL-3.0-or-later.
Original CAD, mounting pattern informed by John Turner's GPLv3 HUB75 bracket.
Candidate: corner offsets inferred from supplied bracket, awaiting measurement.
"""
import sys,math,json
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,MeshPart
out=Path(__file__).resolve().parent
near=10.0;far=33.0;pad=6.0;hole=4.0;plate=3.0;ribheight=3.0;ribwidth=3.0
V=App.Vector

def bar(a,b,width,z,height):
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy);nx=-dy/l*width/2;ny=dx/l*width/2
    points=[V(a[0]+nx,a[1]+ny,z),V(b[0]+nx,b[1]+ny,z),V(b[0]-nx,b[1]-ny,z),V(a[0]-nx,a[1]-ny,z)]
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0,0,height))

doc=App.newDocument('TemporaryPanelXBracket')
solids=[];centres=[]
for sx in [-1,1]:
 for sy in [-1,1]:
    p=[(0,0),(sx*near,sy*far),(sx*far,sy*near)]
    pts=[V(x,y,0) for x,y in p]
    solids.append(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,plate)))
    for a,b in zip(p,p[1:]+p[:1]):solids.append(bar(a,b,2*pad,0,plate))
    for x,y in p:solids.append(Part.makeCylinder(pad,plate,V(x,y,0)))
    solids.append(bar((0,0),(sx*20,sy*20),ribwidth,plate,ribheight))
    solids.append(Part.makeCylinder(ribwidth/2,ribheight,V(sx*20,sy*20,plate)))
    centres.extend(p[1:])
shape=solids[0].multiFuse(solids[1:]).removeSplitter()
for x,y in centres:shape=shape.cut(Part.makeCylinder(hole/2,10,V(x,y,-1)))
shape=shape.removeSplitter()
assert shape.isValid() and len(shape.Solids)==1
obj=doc.addObject('PartDesign::Feature','XBracket');obj.Label='X joint - SOURCE PATTERN - FIT TEST'
obj.Shape=shape
for name,value in [('NearOffset',near),('FarOffset',far),('HoleDiameter',hole),('PlateThickness',plate),('RibHeight',ribheight)]:
 obj.addProperty('App::PropertyLength',name,'Design');setattr(obj,name,value)
obj.addProperty('App::PropertyString','Status');obj.Status='Candidate; verify 20 mm across-seam and 33 mm inward mounting dimensions before printing'
obj.addProperty('App::PropertyString','Regenerate');obj.Regenerate='Edit near/far parameters in build_x_bracket.py and rerun; properties are descriptive, not live constraints.'
s=doc.addObject('Spreadsheet::Sheet','Dimensions')
for i,(a,b) in enumerate([('STATUS','FIT TEST CANDIDATE'),('Panel gap mm',0),('Near hole offset mm',near),('Far hole offset mm',far),('Across-seam centres mm',2*near),('Outer centres mm',2*far),('Hole diameter mm',hole),('Base thickness mm',plate),('Overall height mm',plate+ribheight),('Overall width/height mm',2*(far+pad)),('Full 4x4 interior junctions',9),('Caution','Hole geometry inferred; actual rear clearances unverified')],1):s.set(f'A{i}',str(a));s.set(f'B{i}',str(b))
doc.recompute();doc.saveAs(str(out/'Flockinator-X-joint-fit-test.FCStd'))
Part.export([obj],str(out/'Flockinator-X-joint-fit-test.step'))
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.05,AngularDeflection=.12,Relative=False)
mesh.write(str(out/'Flockinator-X-joint-fit-test.stl'))
report={'status':'FIT TEST CANDIDATE, hole offsets await owner measurement','bounds_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'volume_mm3':shape.Volume,'valid_solid':shape.isValid(),'solid_count':len(shape.Solids),'hole_centres_mm':centres,'hole_diameter_mm':hole,'plate_mm':plate,'rib_total_height_mm':plate+ribheight,'source_STL_holes_mm':[[-5,-24],[15,-24],[-28,-47],[38,-47]],'inference':'Source paired X centres imply offsets 10 and 33 around X=5; Y junction at -57 is inferred by corner symmetry, not measured. Published DWG suggests 7 and 35 instead.','quantity_for_4x4_internal_junctions':9,'structural_tested':False,'hardware_clearance_tested':False}
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
