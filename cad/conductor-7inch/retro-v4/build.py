"""FreeCAD bundled runtime. Printable enclosure prototype; hardware fit unverified."""
import FreeCAD as A, Part, MeshPart, Draft, math, json
from pathlib import Path
R=Path('/Volumes/devops/flockinator/cad/conductor-7inch/retro-v4');(R/'stl').mkdir(exist_ok=True)
d=A.newDocument('Conductor7RetroV4')
W=195.;H=146.;T=3.;F=22.;ang=25.;D=H*math.cos(math.radians(ang));slope=math.tan(math.radians(ang));beige=(.48,.40,.29)
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,A.Vector(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,A.Vector(x,y,z))
def wedge(x0,x1,y0,y1,z0,extra=0):
 p=[A.Vector(x0,y0,z0),A.Vector(x0,y1,z0),A.Vector(x0,y1,F+slope*y1+extra),A.Vector(x0,y0,F+slope*y0+extra)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(A.Vector(x1-x0,0,0))
def rounded(x,y,z,w,h,th,r):
 s=box(x,y+r,z,w,h-2*r,th)
 if w>2*r:s=s.fuse(box(x+r,y,z,w-2*r,h,th))
 for cx in [x+r,x+w-r]:
  for cy in [y+r,y+h-r]:s=s.fuse(cyl(cx,cy,z,r,th))
 return s.removeSplitter()
def tilt(s):s.rotate(A.Vector(),A.Vector(1,0,0),ang);s.translate(A.Vector(0,0,F));return s
records=[];objects=[]
def add(name,s,color=beige):
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1,name
 o=d.addObject('PartDesign::Feature',name);o.Shape=s;o.ViewObject.ShapeColor=color;o.ViewObject.LineColor=(.16,.13,.09)
 o.addProperty('App::PropertyString','FitStatus');o.FitStatus='PRINTABLE FIT PROTOTYPE ONLY: display/PCB retention, cable reach and actual port positions unverified'
 objects.append(o);return o
# Open-bottom shell; future sensors are omitted and upper bezel remains solid.
extra=3/math.cos(math.radians(ang))
outer=wedge(0,W,0,D,3,extra).common(rounded(0,0,0,W,D,150,4)).removeSplitter()
topedges=[e for e in outer.Edges if all(abs(v.Point.z-(F+slope*v.Point.y+extra))<.001 for v in e.Vertexes)]
outer=outer.makeFillet(.8,topedges)
shell=outer.cut(wedge(T,W-T,T,D-T,2,0))
shell=shell.cut(tilt(rounded(19.5,14,-1,156,88,6,3)))
shell=shell.cut(box(12,D-4,7,102,6,25))
# Long rounded vertical side grille, with equal slot lengths kept below roof.
for yy in range(38,115,6):
 h=min(34,F+slope*yy-16)
 slot=rounded(0,0,0,3,h,6,1.5)
 # local XY slot mapped to world YZ, extrusion along X.
 slot.rotate(A.Vector(),A.Vector(1,1,1),120);slot.translate(A.Vector(W-4,yy,10))
 shell=shell.cut(slot)
# Full-width front horizontal rhythm with rounded slot ends.
for xx in range(20,179,7):
 slot=rounded(0,0,0,3,8,5,1.5)
 slot.rotate(A.Vector(),A.Vector(1,0,0),90);slot.translate(A.Vector(xx,4,8))
 shell=shell.cut(slot)
# Integral corner screw towers for removable bottom plate. Clipped under roof.
centres=[(7,7),(W-7,7),(7,D-7),(W-7,D-7)]
for x,y in centres:
 h=F+slope*y
 tower=cyl(x,y,3,5,h).common(wedge(0,W,0,D,2))
 shell=shell.fuse(tower)
 # Prototype pilot for M3 plastic tapping, not a finished thread or insert hole.
 shell=shell.cut(cyl(x,y,2,1.3,13))
case=add('BeigeUpperHousing',shell)
shell=case.Shape.copy()
# Rounded bold lettering, 0.8 mm raised with shallow 0.15 mm embed for emboss union.
text=Draft.make_shapestring(String='FLOCKINATOR',FontFile='/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf',Size=10,Tracking=1.2)
d.recompute()
letters=text.Shape.copy(); bb=letters.BoundBox
letters.translate(A.Vector((W-bb.XLength)/2-bb.XMin,119-bb.YMin,2.85))
letters=tilt(letters.extrude(A.Vector(0,0,.95)))
text.Visibility=False
letterobj=d.addObject('PartDesign::Feature','FLOCKINATORColourPart');letterobj.Shape=letters
letterobj.ViewObject.ShapeColor=(.17,.12,.075)
letterobj.addProperty('App::PropertyString','Purpose');letterobj.Purpose='Separate aligned raised letters for multi-colour printing; common coordinates with housing'
embossed=shell.fuse(letters).removeSplitter()
assert embossed.isValid() and len(embossed.Solids)==1
multibody=shell.cut(letters).removeSplitter()
assert multibody.isValid() and len(multibody.Solids)==1
assert multibody.common(letters).Volume<.001
case.Shape=multibody

# Bottom plate with screw clearance and generic adjustable mounting slots.
plate=rounded(0,0,0,W,D,3,2)
for x,y in centres:plate=plate.cut(cyl(x,y,-1,1.7,5))
# Slotted mounting field, no invented v1.6 mounting coordinates.
for x in [24,44,64,84,104,124,144]:
 for y in [38,72,106]:
  slot=box(x-1.7,y, -1,3.4,15,5).fuse(cyl(x,y,-1,1.7,5)).fuse(cyl(x,y+15,-1,1.7,5))
  plate=plate.cut(slot)
bottom=add('RemovableSlottedBase',plate)
# Clearance reference only; never included in print exports.
screen=add('LCDReferenceOnly',tilt(box(15,8,-3.5,165,100,3.5)),(.06,.29,.34))
# Print a cheap aperture/outer-envelope gauge before the full case.
gauge=box(0,0,0,W,H,1.2).cut(rounded(19.5,14,-1,156,88,4,3))
# Narrow the border to reduce first-test filament; same aperture dimensions.
gauge=gauge.common(box(15,9,0,165,98,2))
gaugeobj=add('ScreenApertureFitGauge',gauge)
gaugeobj.Visibility=False
# Export single-colour and aligned two-colour options in assembly coordinates.
# Keep upper housing upright to avoid raised lettering on the print bed.
exports=[('UpperHousingForMulticolour',multibody),('FLOCKINATORColourPart',letters),('UpperHousingEmbossedSingleColour',embossed),('RemovableSlottedBase',plate),('ScreenApertureFitGauge',gauge)]
for name,s in exports:
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.06,AngularDeflection=.12,Relative=False)
 assert mesh.isSolid(),name
 mesh.write(str(R/'stl'/(name+'.stl')))
 records.append({'part':name,'valid_solid':s.isValid(),'solid_count':len(s.Solids),'mesh_solid':mesh.isSolid(),'triangles':mesh.CountFacets,'bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]})
assert case.Shape.common(bottom.Shape).Volume<.001
assert case.Shape.common(screen.Shape).Volume<.001
# Assembly preview.
d.recompute();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(str(R/'dark-beige-assembled.png'),1400,1000,'White')
# Exploded underside view: separate bottom for review, no change to exported plate.
bottom.Placement.Base=A.Vector(0,0,-35)
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(str(R/'dark-beige-exploded.png'),1400,1000,'White')
bottom.Placement.Base=A.Vector()
d.recompute();d.saveAs(str(R/'Conductor-7inch-retro-v4.FCStd'))
Part.export([case,bottom,letterobj],str(R/'Conductor-7inch-retro-v4.STEP'))
(R/'checks.json').write_text(json.dumps({'status':'Printable prototype; hardware fit not established','screen_angle_deg':ang,'shell_width_mm':W,'shell_depth_mm':D,'parts':records,'checks':['Upper/base zero volume overlap','Upper/bare LCD zero volume overlap'],'limitations':['Display retention not designed for full touch module','Board mounts require actual alignment and insulated standoffs','Slots are generic and may not align with all holes','Port bay location unverified for v1.6','No sensor hardware','Outer plan corner radius 4 mm; top perimeter edge roll 0.8 mm; screen aperture corners 3 mm','Text raised 0.8 mm above bezel, separate colour part with 0.15 mm embed','No full cable fit validation','M3 pilot holes require coupon and fastener check']},indent=2))
print(json.dumps(records))
