"""Build corrected T/X joints from extracted Waveshare drawing coordinates.
Run with FreeCAD's bundled Python. No GUI or safe-mode invocation.
GPL-3.0-or-later. Revision 2: 2026-10-10.
"""
import sys,json,math
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part,MeshPart
V=App.Vector
root=Path(__file__).resolve().parent
source=json.loads((root/'panel-hole-coordinates.json').read_text())
pitch=160.0;thickness=3.0;hole_diameter=4.0;rib_height=3.0;rib_width=3.0;pad=6.0

def cylinder(x,y,r,z=0,h=thickness):return Part.makeCylinder(r,h,V(x,y,z))
def bar(a,b,w,z,h):
 dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx=-dy/length*w/2;ny=dx/length*w/2
 pts=[V(a[0]+nx,a[1]+ny,z),V(b[0]+nx,b[1]+ny,z),V(b[0]-nx,b[1]-ny,z),V(a[0]-nx,a[1]-ny,z)]
 return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h))
def capsule(a,b,w,z=0,h=thickness):
 return bar(a,b,w,z,h).fuse(cylinder(*a,w/2,z,h)).fuse(cylinder(*b,w/2,z,h))

def placed_holes(panel_centres):
 holes=[]
 for i,(cx,cy) in enumerate(panel_centres):
  for kind,key in [('edge_M3','M3_edge_holes'),('corner_mount','corner_3p1mm_features')]:
   for record in source[key]:
    x,y=record['center_relative_panel_mm'];x+=cx;y+=cy
    if abs(x)<40 and abs(y)<40:
     holes.append({'xy':[x,y],'kind':kind,'panel_index':i,'drawing_handle':record['entity_handle']})
 return holes

report={'revision':2,'drawing_sha256':source['sha256'],'panel_pitch_mm':pitch,'drawing_shell_mm':159.8,'nominal_shell_gap_at_pitch_mm':.2,'hole_diameter_mm':hole_diameter,'plate_thickness_mm':thickness,'rib_height_mm':rib_height,'status':'Coordinates verified against drawing; physical screw engagement, seating and strength still require a single-part fit check','parts':{}}
for kind in ['T','X']:
 doc=App.newDocument('Corrected'+kind+'Joint')
 centres=[(-pitch/2,pitch/2),(pitch/2,pitch/2)]
 if kind=='X':centres +=[(-pitch/2,-pitch/2),(pitch/2,-pitch/2)]
 holes=placed_holes(centres)
 assert len(holes)==(6 if kind=='T' else 12)
 if kind=='T':
  # Conventional T footprint, crossbar near outer edge, stem along panel seam.
  pieces=[capsule((-35,7),(35,7),12),capsule((-7,7),(-7,35),12),capsule((7,7),(7,35),12),Part.makeBox(14,34,thickness,V(-7,7,0))]
  ribs=[capsule((-29,2.5),(29,2.5),rib_width,thickness,rib_height),capsule((0,3),(0,31),rib_width,thickness,rib_height)]
 else:
  pieces=[]
  for sx in [-1,1]:
   for sy in [-1,1]:
    coords=[(0,0),(sx*7,sy*35),(sx*35,sy*7)]
    pts=[V(x,y,0) for x,y in coords]
    pieces.append(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,thickness)))
    for a,b in zip(coords,coords[1:]+coords[:1]):pieces.append(capsule(a,b,12))
  ribs=[capsule((-29,0),(29,0),rib_width,thickness,rib_height),capsule((0,-29),(0,29),rib_width,thickness,rib_height)]
 shape=pieces[0].multiFuse(pieces[1:]+ribs).removeSplitter()
 for h in holes:
  x,y=h['xy'];shape=shape.cut(cylinder(x,y,hole_diameter/2,-1,10))
 shape=shape.removeSplitter();assert shape.isValid() and len(shape.Solids)==1
 obj=doc.addObject('PartDesign::Feature',kind+'Bracket');obj.Shape=shape;obj.Label=kind+' bracket v2 - drawing aligned'
 obj.addProperty('App::PropertyString','Status');obj.Status=report['status']
 obj.addProperty('App::PropertyString','Source');obj.Source=source['source']
 for name,value in [('PanelPitch',pitch),('HoleDiameter',hole_diameter),('PlateThickness',thickness),('RibHeight',rib_height)]:
  obj.addProperty('App::PropertyLength',name,'Design');setattr(obj,name,value)
 obj.addProperty('App::PropertyString','EditInstructions');obj.EditInstructions='Properties document the generated shape; change script parameters and regenerate to edit.'
 s=doc.addObject('Spreadsheet::Sheet','HoleCentres');s.set('A1','DRAWING-ALIGNED v2 / physical fit unverified');s.set('A2','X mm');s.set('B2','Y mm');s.set('C2','Mount type');s.set('D2','DWG entity')
 for i,h in enumerate(holes,3):
  s.set(f'A{i}',str(h['xy'][0]));s.set(f'B{i}',str(h['xy'][1]));s.set(f'C{i}',h['kind']);s.set(f'D{i}',h['drawing_handle'])
 doc.recompute();base='Flockinator-'+kind+'-joint-v2'
 doc.saveAs(str(root/(base+'.FCStd')));Part.export([obj],str(root/(base+'.step')))
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.1,Relative=False);mesh.write(str(root/(base+'.stl')))
 # Re-import STEP to validate actual exported cylindrical hole centres.
 exported=Part.Shape();exported.read(str(root/(base+'.step')))
 found=set()
 for face in exported.Faces:
  surf=face.Surface
  if isinstance(surf,Part.Cylinder) and abs(surf.Radius-hole_diameter/2)<1e-6:
   found.add((round(surf.Center.x,6),round(surf.Center.y,6)))
 expected={tuple(h['xy']) for h in holes}
 assert found==expected,(kind,found,expected)
 # Rib clearance for a 7 mm washer envelope, independently at each hole.
 washer_collisions=[]
 ribsolid=ribs[0].multiFuse(ribs[1:])
 for h in holes:
  x,y=h['xy'];v=ribsolid.common(cylinder(x,y,3.5,thickness,rib_height)).Volume
  if v>1e-6:washer_collisions.append(h)
 assert not washer_collisions,washer_collisions
 report['parts'][kind]={'files':{ext:base+'.'+ext for ext in ['FCStd','step','stl']},'bounds_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'volume_mm3':shape.Volume,'holes':holes,'valid_solid':True,'exported_step_hole_centres_match_drawing':True,'7mm_washer_rib_collisions':washer_collisions,'quantity_for_4x4':12 if kind=='T' else 9}
# Reproduce old mismatch against the edge-hole coordinates of the corrected X.
old=json.loads((root.parent/'temporary-panel-joints/rejected-v1/validation.json').read_text())
new=[h['xy'] for h in report['parts']['X']['holes'] if h['kind']=='edge_M3']
errors=[min(math.dist(c,d) for d in new) for c in old['hole_centres_mm']]
report['rejected_v1']={'nearest_edge_hole_error_mm':errors,'expected_error_mm':math.sqrt(13),'missing_corner_mount_holes':4}
assert all(abs(e-math.sqrt(13))<1e-6 for e in errors)
(root/'corrected-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:{'bounds_mm':v['bounds_mm'],'holes':len(v['holes']),'STEP_holes_match_drawing':True} for k,v in report['parts'].items()},indent=2))
