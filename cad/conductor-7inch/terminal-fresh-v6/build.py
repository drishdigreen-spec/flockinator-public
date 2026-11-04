"""Fresh terminal study: FreeCAD Part Design, documented provisional hardware fit."""
import FreeCAD as A, Part, Sketcher, math, json
from pathlib import Path
R=Path(__file__).resolve().parent
d=A.newDocument('FlockinatorFreshTerminalV6')
p=d.addObject('Spreadsheet::Sheet','Params')
rows=[('body_w',235,'mm','Design brief: wide terminal'),('body_d',180,'mm','Proposed desk footprint'),('wall',3,'mm','Brief allowed maximum'),('lid_t',2.4,'mm','Brief'),('screen_rake',20,'deg','Brief default from vertical'),('deck_angle',15,'deg','Brief'),('blend_r',8,'mm','Brief R6-15'),('corner_r',6,'mm','Brief R4-10'),('recess_depth',2,'mm','Brief'),('text_depth',.5,'mm','Brief'),('screen_active_w',154.2144,'mm','Bare LCD datasheet'),('screen_active_h',85.92,'mm','Bare LCD datasheet'),('clearance',.3,'mm','Brief'),('camera_d',10.6,'mm','Assumed 10 mm lens plus 0.6'),('screen_base_x',-35,'mm','Proposed massing'),('screen_base_z',26,'mm','Proposed massing'),('screen_plane_h',145,'mm','Screen and label band'),('front_x',-90,'mm','Proposed massing'),('rear_x',90,'mm','Proposed massing'),('floor_z',3,'mm','Base seating'),('front_z',11.263,'mm','15 degree deck'),('top_x',9.463,'mm','130*sin20 -35'),('top_z',148.160,'mm','130*cos20 +26'),('insert_hole_d',4,'mm','Brief; selected insert must be checked'),('insert_boss_d',8,'mm','Provisional >= brief minimum')]
for row,(alias,val,unit,note) in enumerate(rows,2):
 for col,value in [('A',alias),('B',str(val)),('C',unit),('D',note)]:p.set(col+str(row),value)
 p.setAlias('B'+str(row),alias)
p.set('B22','=screen_base_z - (screen_base_x-front_x)*tan(deck_angle)')
p.set('B23','=screen_base_x + screen_plane_h*sin(screen_rake)')
p.set('B24','=screen_base_z + screen_plane_h*cos(screen_rake)')
p.setColumnWidth('A',180);p.setColumnWidth('D',360)
d.recompute()
W=float(p.get('body_w'));X=float(p.get('screen_base_x'));Z=float(p.get('screen_base_z'));topx=float(p.get('top_x'));topz=float(p.get('top_z'));fz=float(p.get('front_z'))
coord_aliases=[]
body=d.addObject('PartDesign::Body','TerminalHousing')
def polySketch(name,pts,placement,expressions=None):
 s=d.addObject('Sketcher::SketchObject',name);body.addObject(s);s.Placement=placement
 for i,(x,y) in enumerate(pts):
  x2,y2=pts[(i+1)%len(pts)];s.addGeometry(Part.LineSegment(A.Vector(x,y,0),A.Vector(x2,y2,0)),False)
 for i in range(len(pts)):
  s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(pts),1))
  cx=s.addConstraint(Sketcher.Constraint('DistanceX',i,1,pts[i][0]));cy=s.addConstraint(Sketcher.Constraint('DistanceY',i,1,pts[i][1]))
  if expressions:s.setExpression('Constraints['+str(cx)+']',expressions[i][0]);s.setExpression('Constraints['+str(cy)+']',expressions[i][1])
  else:
   for suffix,value,index in [('x',pts[i][0],cx),('y',pts[i][1],cy)]:
    row=70+len(coord_aliases);alias=name.lower()+'_'+str(i)+'_'+suffix
    coord_aliases.append(alias)
    p.set('A'+str(row),alias);p.set('B'+str(row),str(value));p.set('C'+str(row),'mm');p.set('D'+str(row),'Provisional design coordinate; not hardware measurement');p.setAlias('B'+str(row),alias)
    s.setExpression('Constraints['+str(index)+']','Params.'+alias)
 d.recompute();return s
side=A.Placement(A.Vector(),A.Rotation(A.Vector(1,0,0),90))
pts=[(-90,3),(90,3),(90,topz),(topx,topz),(X,Z),(-90,fz)]
expr=[('Params.front_x','Params.floor_z'),('Params.rear_x','Params.floor_z'),('Params.rear_x','Params.top_z'),('Params.top_x','Params.top_z'),('Params.screen_base_x','Params.screen_base_z'),('Params.front_x','Params.front_z')]
master=polySketch('SK_Master_Side',pts,side,expr)
pad=body.newObject('PartDesign::Pad','Pad_TerminalMassing');pad.Profile=master;pad.Length=W;pad.Midplane=True;pad.setExpression('Length','Params.body_w');master.Visibility=False;d.recompute()
inner=polySketch('SK_Interior',[(-86,6),(86,6),(86,topz-3),(topx+12,topz-3),(topx+6,topz-15),(X+10,Z+12),(X+14,Z-3),(-86,fz-3)],side)
pocket=body.newObject('PartDesign::Pocket','Pocket_Interior');pocket.Profile=inner;pocket.Length=W-6;pocket.Midplane=True;pocket.setExpression('Length','Params.body_w-2*Params.wall');d.recompute();pad.Visibility=False;inner.Visibility=False
# Screen-face datum, outward normal toward user.
r=math.radians(20)
rot=A.Rotation(A.Vector(0,-1,0),A.Vector(math.sin(r),0,math.cos(r)),A.Vector(-math.cos(r),0,math.sin(r)),'ZXY')
plane=A.Placement(A.Vector(X,W/2,Z),rot)
datum=body.newObject('PartDesign::Plane','Datum_Screen');datum.Placement=plane;datum.Visibility=False
def rectangle(name,u,v,w,h,place):return polySketch(name,[(u,v),(u+w,v),(u+w,v+h),(u,v+h)],place)
def cut(name,sk,length,prior):
 o=body.newObject('PartDesign::Pocket',name);o.Profile=sk;o.Length=length;d.recompute();prior.Visibility=False;sk.Visibility=False
 assert not o.Shape.isNull() and o.Shape.isValid(),name
 return o
recess=rectangle('SK_ScreenRecess',(W-182)/2,12,182,102,plane)
a=cut('Pocket_RecessedScreenPanel',recess,2,pocket)
window=rectangle('SK_ViewingWindow',(W-155.0144)/2,21,155.0144,86.72,plane)
a=cut('Pocket_ScreenViewingWindow',window,14,a)
# Rear recessed connector panel and large provisional access bay.
rear=A.Placement(A.Vector(90,0,0),A.Rotation(A.Vector(0,1,0),A.Vector(0,0,1),A.Vector(1,0,0),'ZXY'))
a=cut('Pocket_RearPanel',rectangle('SK_RearPanel',-65,8,130,32,rear),1.5,a)
a=cut('Pocket_RearPortBay',rectangle('SK_PortBay',-59,11,118,25,rear),12,a)
# Side grille pocket; horizontal slots in a recessed panel.
right=A.Placement(A.Vector(0,-W/2,0),A.Rotation(A.Vector(1,0,0),A.Vector(0,0,1),A.Vector(0,-1,0),'ZXY'))
a=cut('Pocket_GrilleRecess',rectangle('SK_GrilleRecess',-12,18,76,40,right),1.5,a)
for i in range(6):a=cut('Pocket_HorizontalVent_'+str(i+1),rectangle('SK_Vent_'+str(i+1),-5,22+i*5,62,2,right),8,a)
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,A.Vector(x,y,z))
# Preserved owner typography and first-O camera integration.
import Draft
font='$HOME'
lens_diameter=10.0 # PROVISIONAL, inherited from earlier camera concept
lens_clearance=.3
opening_diameter=lens_diameter+2*lens_clearance
# Preserve MonoLisa's baseline and native fixed advance; no per-glyph centring.
cap_height=10.0
advance=cap_height*640/700 # Verified hmtx=640, capHeight=700, upem=1000
camera_cell=14.0
full_width=10*advance+camera_cell
offset=(W-full_width)/2
baseline=120.0
from PySide import QtGui
rawfont=QtGui.QRawFont(font,100)
assert rawfont.isValid()
contours=json.loads((R/'font-contours-clean.json').read_text())
runs=[]
for index,ch in enumerate('FLOCKINATOR'):
 if index==2:continue # Camera replaces this O, no glyph or printed ring.
 start=offset+(index*advance if index<2 else (index-1)*advance+camera_cell)
 glyphfaces=[]
 for polygon in contours[ch]:
  wires=[]
  for loop in [polygon['outer']]+polygon['holes']:
   wires.append(Part.makePolygon([A.Vector(x,y,0) for x,y in loop]))
  glyphfaces.append(Part.makeFace(wires,'Part::FaceMakerBullseye'))
 flat=Part.makeCompound(glyphfaces)
 flat.translate(A.Vector(start,baseline,-.5))
 raw=flat.extrude(A.Vector(0,0,.5))
 solids=list(raw.Solids)
 unified=solids[0]
 for solid in solids[1:]:unified=unified.fuse(solid).removeSplitter()
 runs.extend(list(unified.Solids))
letters=Part.makeCompound(runs)
camera_local=(offset+2*advance+camera_cell/2,baseline+cap_height/2)

cameraCentre=camera_local
cam=body.newObject('Sketcher::SketchObject','SK_CameraInO');cam.Placement=plane
cam.addGeometry(Part.Circle(A.Vector(cameraCentre[0],cameraCentre[1],0),A.Vector(0,0,1),5.3),False)
cam.addConstraint(Sketcher.Constraint('Diameter',0,10.6));cam.addConstraint(Sketcher.Constraint('DistanceX',0,3,cameraCentre[0]));cam.addConstraint(Sketcher.Constraint('DistanceY',0,3,cameraCentre[1]))
a=cut('Pocket_CameraAperture',cam,20,a)
# Open underside for service access, leaving a seating rim.
under=A.Placement(A.Vector(0,0,3),A.Rotation(A.Vector(1,0,0),180))
a=cut('Pocket_BaseServiceOpening',rectangle('SK_BaseOpening',-86,-W/2+3,172,W-6,under),4,a)
insert_centres=[(x,y) for x in [-72,72] for y in [-W/2+5,W/2-5]]
for i,(x,y) in enumerate(insert_centres):
 sk=d.addObject('Sketcher::SketchObject','SK_InsertBoss_'+str(i));body.addObject(sk);sk.Placement=A.Placement(A.Vector(0,0,3),A.Rotation())
 sk.addGeometry(Part.Circle(A.Vector(x,y,0),A.Vector(0,0,1),4),False)
 for con in [Sketcher.Constraint('Diameter',0,8),Sketcher.Constraint('DistanceX',0,3,x),Sketcher.Constraint('DistanceY',0,3,y)]:sk.addConstraint(con)
 boss=body.newObject('PartDesign::Pad','Pad_InsertBoss_'+str(i));boss.Profile=sk;boss.Length=10;d.recompute();a.Visibility=False;sk.Visibility=False;a=boss
 sk=d.addObject('Sketcher::SketchObject','SK_InsertBore_'+str(i));body.addObject(sk);sk.Placement=under
 sk.addGeometry(Part.Circle(A.Vector(x,-y,0),A.Vector(0,0,1),2),False)
 for con in [Sketcher.Constraint('Diameter',0,4),Sketcher.Constraint('DistanceX',0,3,x),Sketcher.Constraint('DistanceY',0,3,-y)]:sk.addConstraint(con)
 a=cut('Pocket_InsertBore_'+str(i),sk,6.5,a)
# Largest blends last on the screen/deck and screen/top meeting lines.
edgeids=[]
for i,e in enumerate(a.Shape.Edges,1):
 b=e.BoundBox
 if b.YLength>200 and b.XLength<.001 and b.ZLength<.001 and ((abs(b.XMin-X)<.01 and abs(b.ZMin-Z)<.01) or (abs(b.XMin-topx)<.01 and abs(b.ZMin-topz)<.01)):edgeids.append('Edge'+str(i))
fil=body.newObject('PartDesign::Fillet','Fillet_PlaneBlends');fil.Base=(a,edgeids);fil.Radius=8;fil.setExpression('Radius','Params.blend_r');d.recompute()
assert not fil.Shape.isNull() and fil.Shape.isValid(),'Blend failed'
a.Visibility=False
# Matching R6 rounds on the rear corners AND the short front-lip corners.
ids=[]
for i,e in enumerate(fil.Shape.Edges,1):
 b=e.BoundBox
 if b.ZLength>5 and b.XLength<.001 and b.YLength<.001 and abs(abs(b.XMin)-90)<.01 and abs(abs(b.YMin)-W/2)<.01:ids.append('Edge'+str(i))
corner=body.newObject('PartDesign::Fillet','Fillet_OuterCorners');corner.Base=(fil,ids);corner.Radius=6;corner.setExpression('Radius','Params.corner_r');d.recompute()
assert not corner.Shape.isNull() and corner.Shape.isValid(),'Corner fillet failed'
fil.Visibility=False
corner.ViewObject.ShapeColor=(.78,.72,.60);corner.ViewObject.LineColor=(.18,.15,.11)
body.Tip=corner
master.Visibility=False;datum.Visibility=False
d.recompute();Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
d.saveAs(str(R/'FLOCKINATOR_Fresh_v06.FCStd'))
Gui.activeDocument().activeView().saveImage(str(R/'fresh-shell.png'),1400,1000,'White')
print('Fresh Part Design shell valid; master DOF',master.FullyConstrained,'bounds',corner.Shape.BoundBox)
# Inlay operations are the brief's permitted Part Boolean exception.
def transformed(shape):
 s=shape.copy();s.Placement=plane.multiply(s.Placement);return s
lettershape=transformed(letters)
host=corner.Shape.cut(lettershape).removeSplitter()
assert host.isValid() and len(host.Solids)==1
inlaycut=body.newObject('PartDesign::Feature','Cut_TextInlay');inlaycut.Shape=host;corner.Visibility=False
inlaycut.addProperty('App::PropertyString','OperationNote');inlaycut.OperationNote='Permitted inlay boolean; 0.5 mm recessed, no raised text'
inlaycut.ViewObject.ShapeColor=(.78,.72,.60)
def partBody(name,shape,color):
 b=d.addObject('PartDesign::Body',name);f=b.newObject('PartDesign::Feature',name+'_Geometry');f.Shape=shape;f.ViewObject.ShapeColor=color;f.ViewObject.LineColor=(.14,.12,.1)
 assert shape.isValid();return b,f
accent=(.169,.149,.133)
tb,textpart=partBody('Text_Inlay',lettershape,accent)
# Dark bezel panel floor, separate flush accent inlay at 2 mm recess.
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,A.Vector(x,y,z))
ring=box((W-182)/2,12,-2,182,102,.5).cut(box((W-155.0144)/2,21,-3,155.0144,86.72,3))
bb,bezel=partBody('Bezel_Inlay',transformed(ring),accent)
# Visual screen sits below the bezel surface. Reference only.
rb,glass=partBody('Display_REFERENCE_ONLY',transformed(box((W-154.2144)/2,21.4,-2.8,154.2144,85.92,.5)),(.035,.22,.20))
glass.addProperty('App::PropertyString','Status');glass.Status='Bare active-area visual only; complete touch glass and mounting unverified'
lb,lens=partBody('Lens_REFERENCE_ONLY',transformed(cyl(cameraCentre[0],cameraCentre[1],-3,5,2.7)),(.03,.03,.035))
# Base plate is a native Pad and corner fillet, all bottom fasteners hidden.
basebody=d.addObject('PartDesign::Body','Base')
base_sk=d.addObject('Sketcher::SketchObject','SK_Base');basebody.addObject(base_sk)
coords=[(-90,-W/2),(90,-W/2),(90,W/2),(-90,W/2)]
for i,pt in enumerate(coords):
 q=coords[(i+1)%4];idx=base_sk.addGeometry(Part.LineSegment(A.Vector(pt[0],pt[1],0),A.Vector(q[0],q[1],0)),False)
 base_sk.addConstraint(Sketcher.Constraint('Block',idx))
basepad=basebody.newObject('PartDesign::Pad','Pad_Base');basepad.Profile=base_sk;basepad.Length=3;basepad.setExpression('Length','Params.wall');d.recompute();base_sk.Visibility=False
holes=d.addObject('Sketcher::SketchObject','SK_BaseScrewClearances');basebody.addObject(holes);holes.Placement=A.Placement(A.Vector(0,0,3),A.Rotation())
for x,y in insert_centres:
 i=holes.addGeometry(Part.Circle(A.Vector(x,y,0),A.Vector(0,0,1),1.7),False)
 for c in [Sketcher.Constraint('Diameter',i,3.4),Sketcher.Constraint('DistanceX',i,3,x),Sketcher.Constraint('DistanceY',i,3,y)]:holes.addConstraint(c)
baseholes=basebody.newObject('PartDesign::Pocket','Pocket_BaseScrewClearances');baseholes.Profile=holes;baseholes.Length=3;d.recompute();basepad.Visibility=False;holes.Visibility=False
vertical=[]
for i,e in enumerate(baseholes.Shape.Edges,1):
 if e.BoundBox.ZLength>2.9 and abs(e.BoundBox.XMin)>89 and abs(e.BoundBox.YMin)>W/2-1:vertical.append('Edge'+str(i))
basefil=basebody.newObject('PartDesign::Fillet','Fillet_BaseCorners');basefil.Base=(baseholes,vertical);basefil.Radius=6;d.recompute();assert basefil.Shape.isValid();baseholes.Visibility=False;basefil.ViewObject.ShapeColor=accent
# Preserve visibly separate plinth rather than a snap-on top facade.
for o in d.Objects:
 if o.TypeId=='Sketcher::SketchObject' or o.Name.startswith('ShapeString') or o.TypeId=='PartDesign::Plane':o.Visibility=False
body.Tip=inlaycut;basebody.Tip=basefil
inlaycut.Visibility=True;textpart.Visibility=True;bezel.Visibility=True;glass.Visibility=True;lens.Visibility=True
# Front-oriented isometric view (front is negative X).
Gui.activeDocument().activeView().viewAxonometric()
ori=Gui.activeDocument().activeView().getCameraOrientation()
Gui.activeDocument().activeView().setCameraOrientation(A.Rotation(A.Vector(0,0,1),180).multiply(ori).Q)
Gui.activeDocument().activeView().fitAll()
d.recompute();d.saveAs(str(R/'FLOCKINATOR_Fresh_v06.FCStd'))
Gui.activeDocument().activeView().saveImage(str(R/'fresh-terminal.png'),1600,1100,'White')
Part.export([inlaycut,basefil,textpart,bezel],str(R/'FLOCKINATOR_Fresh_v06.step'))
print('Fresh assembly saved, all bodies valid; font inlay at -0.5 mm, bezel floor -2 mm.')
