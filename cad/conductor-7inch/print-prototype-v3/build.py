"""FreeCAD bundled runtime. Printable enclosure prototype; hardware fit unverified."""
import FreeCAD as A, Part, MeshPart, math, json
from pathlib import Path
R=Path('/Volumes/devops/flockinator/cad/conductor-7inch/print-prototype-v3');(R/'stl').mkdir(exist_ok=True)
d=A.newDocument('Conductor7BeigePrototypeV3')
W=195.;H=146.;T=3.;F=22.;ang=25.;D=H*math.cos(math.radians(ang));slope=math.tan(math.radians(ang));beige=(.48,.40,.29)
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,A.Vector(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,A.Vector(x,y,z))
def wedge(x0,x1,y0,y1,z0,extra=0):
 p=[A.Vector(x0,y0,z0),A.Vector(x0,y1,z0),A.Vector(x0,y1,F+slope*y1+extra),A.Vector(x0,y0,F+slope*y0+extra)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(A.Vector(x1-x0,0,0))
def tilt(s):s.rotate(A.Vector(),A.Vector(1,0,0),ang);s.translate(A.Vector(0,0,F));return s
records=[];objects=[]
def add(name,s,color=beige):
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1,name
 o=d.addObject('PartDesign::Feature',name);o.Shape=s;o.ViewObject.ShapeColor=color;o.ViewObject.LineColor=(.16,.13,.09)
 o.addProperty('App::PropertyString','FitStatus');o.FitStatus='PRINTABLE FIT PROTOTYPE ONLY: display/PCB retention, cable reach and actual port positions unverified'
 objects.append(o);return o
# Open-bottom shell; future sensors are omitted and upper bezel remains solid.
shell=wedge(0,W,0,D,3).cut(wedge(T,W-T,T,D-T,2,10))
shell=shell.cut(box(12,D-4,7,102,6,25))
for yy in range(72,102,5):shell=shell.cut(box(W-4,yy,13,6,2,23))
for xx in range(20,75,7):shell=shell.cut(box(xx,-1,8,3,5,6))
roof=tilt(box(0,0,0,W,H,3).cut(box(19.5,14,-1,156,88,5)))
shell=shell.fuse(roof)
# Integral corner screw towers for removable bottom plate. Clipped under roof.
centres=[(7,7),(W-7,7),(7,D-7),(W-7,D-7)]
for x,y in centres:
 h=F+slope*y
 tower=cyl(x,y,3,5,h).common(wedge(0,W,0,D,2))
 shell=shell.fuse(tower)
 # Prototype pilot for M3 plastic tapping, not a finished thread or insert hole.
 shell=shell.cut(cyl(x,y,2,1.3,13))
case=add('BeigeUpperHousing',shell)
# Bottom plate with screw clearance and generic adjustable mounting slots.
plate=box(0,0,0,W,D,3)
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
gauge=box(0,0,0,W,H,1.2).cut(box(19.5,14,-1,156,88,4))
# Narrow the border to reduce first-test filament; same aperture dimensions.
gauge=gauge.common(box(15,9,0,165,98,2))
gaugeobj=add('ScreenApertureFitGauge',gauge)
gaugeobj.Visibility=False
# Export each part in proposed printing orientation, all resting on Z=0.
for o in [case,bottom,gaugeobj]:
 s=o.Shape.copy()
 if o==case:
  # Front/bezel face on bed. This prototype requires internal supports.
  s.translate(A.Vector(0,0,-F));s.rotate(A.Vector(),A.Vector(1,0,0),-ang);s.rotate(A.Vector(),A.Vector(1,0,0),180)
 s.translate(A.Vector(-s.BoundBox.XMin,-s.BoundBox.YMin,-s.BoundBox.ZMin))
 mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,AngularDeflection=.15,Relative=False)
 assert mesh.isSolid(),o.Name
 mesh.write(str(R/'stl'/(o.Name+'.stl')))
 records.append({'part':o.Name,'valid_solid':o.Shape.isValid(),'mesh_closed':mesh.isSolid(),'mesh_solid':mesh.isSolid(),'triangles':mesh.CountFacets,'print_bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]})
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
d.recompute();d.saveAs(str(R/'Conductor-7inch-dark-beige-v3.FCStd'))
Part.export([case,bottom],str(R/'Conductor-7inch-dark-beige-v3.STEP'))
(R/'checks.json').write_text(json.dumps({'status':'Printable prototype; hardware fit not established','screen_angle_deg':ang,'shell_width_mm':W,'shell_depth_mm':D,'parts':records,'checks':['Upper/base zero volume overlap','Upper/bare LCD zero volume overlap'],'limitations':['Display retention not designed for full touch module','Board mounts require actual alignment and insulated standoffs','Slots are generic and may not align with all holes','Port bay location unverified for v1.6','No sensor hardware','No full cable fit validation','M3 pilot holes require coupon and fastener check']},indent=2))
print(json.dumps(records))
