"""FreeCAD bundled runtime: visual layout study, all unmeasured geometry labelled."""
import FreeCAD as A, Part, math, json
from pathlib import Path
R=Path('/Volumes/devops/flockinator/cad/conductor-7inch/flat-board-v2')
d=A.newDocument('Conductor7FlatBoardV2')
W=195.;H=146.;t=3.;angle=25.;front=22.;D=H*math.cos(math.radians(angle));m=math.tan(math.radians(angle))
records=[]; parts=[]
def box(x,y,z,w,h,v):return Part.makeBox(w,h,v,A.Vector(x,y,z))
def wedge(x0,x1,y0,y1,z0,over=0):
 p=[A.Vector(x0,y0,z0),A.Vector(x0,y1,z0),A.Vector(x0,y1,front+m*y1+over),A.Vector(x0,y0,front+m*y0+over)]
 return Part.Face(Part.makePolygon(p+[p[0]])).extrude(A.Vector(x1-x0,0,0))
def tilt(s):
 s.rotate(A.Vector(),A.Vector(1,0,0),angle);s.translate(A.Vector(0,0,front));return s
spec='CONCEPT ONLY: estimated layout, not measured v1.6 mounting geometry'
def add(name,s,c,note=spec):
 s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1,name
 o=d.addObject('PartDesign::Feature',name);o.Shape=s;o.addProperty('App::PropertyString','Status');o.Status=note;o.ViewObject.ShapeColor=c;o.ViewObject.LineColor=(.08,.09,.1);parts.append(o)
 records.append({'part':name,'valid':True,'solids':1,'volume_mm3':s.Volume});return o
# Base shell, rear openings remain permanently accessible.
shell=wedge(0,W,0,D,0).cut(wedge(t,W-t,t,D-t,t,10))
# Wide rear port bay, deliberately not individual fitted holes.
shell=shell.cut(box(12,D-4,7,102,6,25))
# Side speaker grille, right wall.
for yy in range(72,102,5):shell=shell.cut(box(W-4,yy,13,6,2,23))
for xx in range(20,75,7):shell=shell.cut(box(xx,-1,8,3,5,6))
base=add('WedgeBase',shell,(.19,.23,.28))
# Bezel: screen and camera apertures, dimensions provisional.
bezel=box(0,0,0,W,H,3).cut(box(19.5,14,-1,156,88,5))
bezel=bezel.cut(Part.makeCylinder(5,5,A.Vector(W/2,128,-1)))
face=add('ScreenAndCameraBezel',tilt(bezel),(.29,.34,.4))
lcd=add('BareLCDReference',tilt(box(15,8,-3.5,165,100,3.5)),(.06,.28,.36),'165 x 100 x 3.5 mm datasheet LCD; touch glass and adapter omitted')
# Active screen indication is flush with the aperture, decorative only.
active=add('ScreenSurface',tilt(box(19.5,14,0,156,88,.4)),(.07,.43,.54),'Visual screen surface, not physical touch-glass geometry')
# PCB dimensions retained conservatively from older drawing, horizontal mounting.
py=D-82
pcb=add('FlatEVBoardReference',box(15,py,8,88,74,1.6),(.08,.39,.22),'88 x 74 mm rectangular bounding reference from older drawing; v1.6 exact outline/mounts unknown')
chip=add('ComponentHeightAllowance',box(30,py+15,9.6,55,40,14),(.2,.23,.25),'Illustrative component envelope; height unmeasured')
ports=[]
for name,x,w,h in [('USB_A',20,13,7),('USB_C_1',39,9,4),('USB_C_2',54,9,4),('USB_C_3',69,9,4),('Ethernet',84,16,14)]:
 ports.append(add(name,box(x,D-19,9.6,w,20,h),(.65,.68,.7),'Illustrative port location/size only; verify v1.6 coordinates, plug and latch envelopes'))
# Side-firing speaker: square body plus conservative ear allowance.
sp=add('SpeakerBody',box(177,72,9,15,31,31),(.7,.39,.12),'Owner body 31 x 31 x 15 mm, cone faces right; 4 ohm 3 W')
ears=add('SpeakerEarClearance',box(177,65.5,9,15,44,31),(.9,.63,.24),'Conservative overall ear envelope; no hole coordinates inferred');ears.ViewObject.Transparency=80
cone=add('SpeakerConeIndicator',Part.makeCylinder(12,1,A.Vector(192,87.5,24.5),A.Vector(1,0,0)),(.17,.17,.18),'Visual cone indication only')
# Camera sensor and separate adapter are unmeasured planning volumes.
sensor=add('CameraSensorAllowance',tilt(box(W/2-12,116,-8,24,24,6)),(.32,.5,.25),'ASSUMED 24 x 24 x 6 mm planning allowance; replace with measured camera sensor')
lens=add('CameraLensIndicator',tilt(Part.makeCylinder(4.5,5,A.Vector(W/2,128,-2))),(.08,.08,.09),'Illustrative lens only; optical direction/FOV not established')
adapt=add('CameraAdapterAllowance',box(120,py+25,8,30,30,3),(.46,.31,.6),'ASSUMED 30 x 30 x 3 mm camera adapter planning allowance; no fitted mounts')
# Ribbon routes are schematic guide wires, not cables of validated length.
routes=[]
for name,coords in [('DisplayRibbonRoute',[(60,py+8,24),(60,py,30),(65,42,36),(70,35,front+m*35-5)]),('CameraRibbonRoute',[(125,py+38,12),(130,92,28),(120,115,58),(98,116,front+m*116-7)]),('PowerHarnessRoute',[(90,py+12,15),(112,60,20),(130,35,33)])]:
 o=d.addObject('PartDesign::Feature',name);o.Shape=Part.makePolygon([A.Vector(*c) for c in coords]);o.ViewObject.LineColor=(.95,.64,.18);o.ViewObject.LineWidth=3;o.addProperty('App::PropertyString','Status');o.Status='Schematic route only: actual cable length/bend radius/connector ends unverified';routes.append(o)
# Explicit physical clearances for separated major planning volumes.
checks=[]
for u,v in [(base,pcb),(face,pcb),(lcd,pcb),(base,sp),(lcd,sp),(pcb,sp),(pcb,adapt),(lcd,sensor),(face,sensor)]:
 vol=u.Shape.common(v.Shape).Volume;assert vol<.001,(u.Name,v.Name,vol);checks.append({'parts':[u.Name,v.Name],'overlap_mm3':vol})
d.recompute()
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
# Outer view: no schematic internals showing through enclosure.
for o in [ears]+routes:o.Visibility=False
Gui.activeDocument().activeView().saveImage(str(R/'assembled.png'),1400,1000,'White')
# Internal view: remove upper shell and display; retain camera/speaker/PCB.
for o in [face,lcd,active]:o.Visibility=False
base.ViewObject.Transparency=85
ears.Visibility=True
for o in routes:o.Visibility=True
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(str(R/'internal-layout.png'),1400,1000,'White')
# Rear view to show permanent port opening.
for o in [face,lcd,active]:o.Visibility=True
base.ViewObject.Transparency=0;ears.Visibility=False
for o in routes:o.Visibility=False
Gui.activeDocument().activeView().setCameraOrientation(A.Rotation(A.Vector(0,0,1),180).multiply(A.Rotation(A.Vector(1,0,0),60)).Q)
Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(str(R/'rear-ports.png'),1400,1000,'White')
# Saved document opens in the useful internal view.
for o in [face,lcd,active]:o.Visibility=False
base.ViewObject.Transparency=85
for o in routes:o.Visibility=True
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
d.recompute();d.saveAs(str(R/'Conductor-7inch-flat-board-v2.FCStd'))
Part.export(parts,str(R/'Conductor-7inch-flat-board-v2.STEP'))
(R/'checks.json').write_text(json.dumps({'status':'Visual layout concept only; not print-ready','width_mm':W,'depth_mm':D,'front_height_mm':front,'rear_height_mm':front+m*D,'screen_angle_degrees':angle,'parts':records,'checks':checks,'limitations':['PCB v1.6 geometry unmeasured','Full touch assembly and adapter omitted','Camera allowances assumed','Port positions illustrative','Cable reach and bend clearances not validated','Fasteners and retention not designed']},indent=2))
print('Saved v2 concept, STEP, three images and checks. All major clearance checks passed.')
