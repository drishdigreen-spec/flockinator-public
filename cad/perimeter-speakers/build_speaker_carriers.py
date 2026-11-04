"""FreeCAD bundled Python: extend the physically proven v2 T solid.
Coordinates: X along edge, Y inward over panels, +Z rearward toward whiteboard.
GPL-3.0-or-later. Speaker reference geometry is separately CC BY 4.0.
"""
from pathlib import Path
import sys,json,math
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,MeshPart
V=App.Vector
root=Path(__file__).resolve().parent;out=root/'carriers-v1';out.mkdir(exist_ok=True)
original=Part.Shape();original.read(str(root.parent/'panel-hole-review/Flockinator-T-joint-v2.step'))
panelholes=json.loads((root.parent/'panel-hole-review/corrected-validation.json').read_text())['parts']['T']['holes']
# Confirmed speaker envelope. Front face of flange is mounted against pad rear face.
speaker_y=-37.4;flange_front_z=-3.0;pad_front_z=-6.0;pad_thickness=3.0
speaker_z=flange_front_z+2.15 # source Z=2.15 becomes world -3 after front/back inversion
hole_diameter=4.0;pad_radius=6.0;rail_y=-10.0

def cylinder(x,y,r,z,h):return Part.makeCylinder(r,h,V(x,y,z))
def bar(a,b,width,z,height):
 dx,dy=b[0]-a[0],b[1]-a[1];d=math.hypot(dx,dy);nx=-dy/d*width/2;ny=dx/d*width/2
 pts=[V(a[0]+nx,a[1]+ny,z),V(b[0]+nx,b[1]+ny,z),V(b[0]-nx,b[1]-ny,z),V(a[0]-nx,a[1]-ny,z)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,height))
def capsule(a,b,width,z,height):return bar(a,b,width,z,height).fuse(cylinder(*a,width/2,z,height)).fuse(cylinder(*b,width/2,z,height))
def leg(x):
 # Stay behind panel plane until clear of Y=0 edge; then step toward front.
 yz=[(4,0),(4,3),(-4,3),(-10,-3),(-13,-3),(-13,-6),(-10,-6),(-4,0)]
 pts=[V(x-4,y,z) for y,z in yz]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(8,0,0))
report={'status':'Prototype geometry; speaker dimensions owner-confirmed, carrier print/fit not yet tested','speaker_body_mm':[99.5,44.8,21.2987],'speaker_mount_pattern_mm':[90,36],'source_T':'../panel-hole-review/Flockinator-T-joint-v2.step','coordinate_convention':'X along panel edge, +Y inward, +Z rearward','speaker_flange_front_face_z':flange_front_z,'speaker_rearmost_z':speaker_z+9,'nominal_whiteboard_z_assumption':12,'nominal_whiteboard_clearance_mm':12-(speaker_z+9),'speaker_body_gap_to_panel_edge_mm':15,'bracket_speaker_hole_diameter_mm':hole_diameter,'fastener_basis':'Provisional M3 with broad washers appropriate to the actual speaker lugs/grommets; model flange opening 6.3 mm is not an M6 thread specification.','parts':{}}
for variant,centres in [('single-left',[-20]),('single-right',[20]),('twin',[-55,55])]:
 mounts=[(cx+dx,speaker_y+18) for cx in centres for dx in [-45,45]]
 rail_min=min(-23,min(x for x,y in mounts));rail_max=max(23,max(x for x,y in mounts))
 parts=[original,leg(-23),leg(23),capsule((rail_min,rail_y),(rail_max,rail_y),6,pad_front_z,6)]
 for x,y in mounts:parts.append(capsule((x,rail_y),(x,y),2*pad_radius,pad_front_z,pad_thickness))
 shape=parts[0].multiFuse(parts[1:]).removeSplitter()
 for x,y in mounts:shape=shape.cut(cylinder(x,y,hole_diameter/2,-8,12))
 # Pair of 3 mm lacing holes for a small cable tie, outside the original T.
 for x in [-5,5]:shape=shape.cut(cylinder(x,rail_y,1.5,-8,12))
 shape=shape.removeSplitter();assert shape.isValid() and len(shape.Solids)==1
 # Keep every original contact/mounting feature. No forward intrusion over panels.
 assert original.cut(shape).Volume<1e-5
 panel_front_volume=Part.makeBox(500,200,30,V(-250,0,-30))
 assert shape.common(panel_front_volume).Volume<1e-6
 # Panel screw access from rear, 7 mm washer/tool envelope.
 for h in panelholes:
  x,y=h['xy'];assert shape.common(cylinder(x,y,3.5,3.01,20)).Volume<1e-6
 # Model cone envelopes (both drivers) remain clear of carrier.
 for cx in centres:
  for dx in [-20.9,20.9]:assert shape.common(cylinder(cx+dx,speaker_y,17.8,-14,11)).Volume<1e-6
 # Verify speaker mounting hole and washer areas are outside cones and rail.
 for x,y in mounts:
  assert shape.common(cylinder(x,y,4.5,pad_front_z-5,4.99)).Volume<1e-6
 doc=App.newDocument('SpeakerCarrier'+variant.replace('-',''))
 obj=doc.addObject('PartDesign::Feature','Carrier');obj.Shape=shape;obj.Label='T speaker carrier / '+variant+' / FIT TEST'
 obj.addProperty('App::PropertyString','Status');obj.Status=report['status']
 obj.addProperty('App::PropertyString','PreservedInterface');obj.PreservedInterface='Original v2 T solid retained; panel mounting holes unchanged'
 sheet=doc.addObject('Spreadsheet::Sheet','Dimensions')
 rows=[('Variant',variant),('Speaker centres X mm',str(centres)),('Speaker centre Y mm',speaker_y),('Speaker mount row Y mm',speaker_y+18),('Mount hole separation mm',90),('Clearance holes mm',4),('Flange front Z mm',-3),('Rear speaker envelope Z mm',speaker_z+9),('Whiteboard assumed Z mm',12),('Nominal clearance mm',12-(speaker_z+9)),('STATUS','FIT TEST - verify hardware and whiteboard clearance')]
 for i,(a,b) in enumerate(rows,1):sheet.set(f'A{i}',str(a));sheet.set(f'B{i}',str(b))
 doc.recompute();stem='Flockinator-T-speaker-'+variant+'-v1'
 doc.saveAs(str(out/(stem+'.FCStd')));Part.export([obj],str(out/(stem+'.step')))
 # Orient print export: panel rear/rib plane on bed at Z=0, speaker pads above.
 printable=shape.copy();printable.rotate(V(0,0,0),V(1,0,0),180);printable.translate(V(0,0,6))
 mesh=MeshPart.meshFromShape(Shape=printable,LinearDeflection=.03,AngularDeflection=.12,Relative=False);mesh.write(str(out/(stem+'.stl')))
 exported=Part.Shape();exported.read(str(out/(stem+'.step')))
 actual=set()
 for f in exported.Faces:
  surf=f.Surface
  if isinstance(surf,Part.Cylinder) and abs(surf.Radius-2)<1e-5:actual.add((round(surf.Center.x,4),round(surf.Center.y,4)))
 expected={tuple(h['xy']) for h in panelholes}|{(round(x,4),round(y,4)) for x,y in mounts};assert actual==expected,(actual,expected)
 report['parts'][variant]={'stem':stem,'quantity':4,'speaker_centres_x_mm':centres,'speaker_mounts_xy_mm':mounts,'bounds_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'volume_mm3':shape.Volume,'valid_solid':True,'original_T_preserved':True,'STEP_holes_match':True,'STL_transform':'180 degrees about X then translate Z +6 mm; print orientation differs from assembly STEP','print_requires_supports':True}
(root/'carrier-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
