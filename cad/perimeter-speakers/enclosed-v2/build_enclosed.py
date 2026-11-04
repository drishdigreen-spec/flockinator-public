"""Independent Flockinator enclosure geometry; GPL-3.0-or-later.
Run using FreeCAD bundled Python. Original lual mesh is not incorporated.
Coordinates: front -Z, whiteboard +Z, panel inward +Y.
"""
from pathlib import Path
import sys, math, json
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part, MeshPart
V=A.Vector
root=Path(__file__).resolve().parent; out=root/'parts';out.mkdir(exist_ok=True)
source=root.parent.parent/'panel-hole-review/Flockinator-T-joint-v2.step'
original=Part.Shape();original.read(str(source))
panelholes=json.loads((source.parent/'corrected-validation.json').read_text())['parts']['T']['holes']
# Local module: front Z=0, rear Z=40. Global translation (cx, -37, -35).
W,H=116.,62.; mounts=[(x,y) for x in [-53.,53.] for y in [-26.,26.]]
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def rounded(w,h,r,z,d):
 s=box(-w/2+r,-h/2,z,w-2*r,h,d).fuse(box(-w/2,-h/2+r,z,w,h-2*r,d))
 for x in [-w/2+r,w/2-r]:
  for y in [-h/2+r,h/2-r]:s=s.fuse(cyl(x,y,z,r,d))
 return s.removeSplitter()
def moved(s,cx=0):
 s=s.copy();s.translate(V(cx,-37,-35));return s

def bored(s,z,h):
 for x,y in mounts:s=s.cut(cyl(x,y,z,1.7,h))
 return s.removeSplitter()
# Surrounding shell, 6 mm nominal walls; front seating lip 2 mm deep.
body=rounded(W,H,5,3,33).cut(rounded(104,50,4,5,32)).cut(rounded(94,40,3,2,4))
body=bored(body,2,36)
# Top cable exit open to rear cover seam: 6 mm wide, 3 mm deep.
body=body.cut(box(-3,24,33,6,9,4)).removeSplitter()
# Separate front guard: hexagonal holes, central window only.
grille=rounded(W,H,5,0,3)
window=rounded(94,40,3,-1,5)
hexes=[];R=3.7;pitchR=4.5
for row in range(-4,5):
 for col in range(-9,10):
  cx=math.sqrt(3)*pitchR*(col+.5*(row%2));cy=1.5*pitchR*row
  points=[V(cx+R*math.cos(math.radians(30+60*i)),cy+R*math.sin(math.radians(30+60*i)),-1) for i in range(6)]
  h=Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0,0,5))
  if h.cut(window).Volume<1e-7:hexes.append(h)
grille=grille.cut(Part.makeCompound(hexes));grille=bored(grille,-1,5)
# Rear retaining ring; foam shims against the rigid rear rim, not diaphragms.
retainer=rounded(102,48,2,29,2.5).cut(rounded(90,36,2,28,5)).removeSplitter()
# Rear lid with recessed M3 hex nuts. Four pillars locate the retaining frame.
lid=rounded(W,H,5,36,4)
for x,y in mounts:
 rad=5.8/math.sqrt(3);pts=[V(x+rad*math.cos(math.pi/3*i),y+rad*math.sin(math.pi/3*i),37.4) for i in range(6)]
 nut=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,4))
 lid=lid.cut(nut).cut(cyl(x,y,35,1.7,7))
for x in [-48,48]:
 for y in [-21,21]:lid=lid.fuse(box(x-2,y-2,31.5,4,4,4.5))
lid=lid.removeSplitter()
# Solid envelope used for clearances; not a detailed speaker reconstruction.
speaker=rounded(99.5,44.8,2,6,21.3)
fibre=box(-40,-13,30.5,80,26,5)
assert body.common(speaker).Volume<1e-6
assert grille.common(speaker).Volume<1e-6
assert retainer.common(speaker).Volume<1e-6
assert lid.common(speaker).Volume<1e-6
assert body.common(fibre).Volume+retainer.common(fibre).Volume+lid.common(fibre).Volume<1e-6
report={'status':'First-fit enclosure prototype; CAD checks only, not physically fitted or sliced','print_settings':{'infill_pattern':'gyroid','infill_percent':50,'wall_loops':5},'module_outer_mm':[W,H,40],'cavity_xy_mm':[104,50],'speaker_design_envelope_mm':[99.5,44.8,21.3],'speaker_owner_envelope_mm':[98,44,20],'speaker_global_front_z':-29,'speaker_global_rear_z':-7.7,'grille_inner_z':-32,'nominal_grille_clearance_mm':3,'rear_cover_global_z':5,'assumed_whiteboard_z':12,'nominal_board_clearance_mm':7,'loose_fibre_pad_envelope_mm':[80,26,5],'fibre_note':'Clearance reservation only: secure loosely, keep material clear of vents and diaphragms; no measured acoustic claim.','hex_openings':len(hexes),'hex_open_area_within_94x40_window_percent':sum(s.Volume/5 for s in hexes)/(94*40)*100,'twin_spacing_mm':118,'twin_case_gap_mm':2,'single_to_twin_case_gap_mm':5,'parts':{},'checks':{'speaker_envelope_clear':True,'fibre_envelope_clear':True}}
shapes={}
def export(name,shape,quantity,orient='front',support=False):
 assert shape.isValid() and len(shape.Solids)==1,name
 shapes[name]=shape
 doc=A.newDocument(name.replace('-','_'));o=doc.addObject('PartDesign::Feature','Part');o.Label=name;o.Shape=shape
 o.addProperty('App::PropertyString','PrototypeStatus');o.PrototypeStatus=report['status']
 for prop,val in [('Infill','Gyroid 50%'),('WallLoops','5'),('SupportNote','Supports required; inspect slicer' if support else 'Suggested orientation supplied; inspect slicer')]:o.addProperty('App::PropertyString',prop);setattr(o,prop,val)
 doc.recompute();stem='Flockinator-'+name+'-v2';doc.saveAs(str(out/(stem+'.FCStd')));Part.export([o],str(out/(stem+'.step')))
 p=shape.copy()
 if orient=='rear':p.rotate(V(0,0,0),V(1,0,0),180)
 p.translate(V(0,0,-p.BoundBox.ZMin))
 mesh=MeshPart.meshFromShape(Shape=p,LinearDeflection=.04,AngularDeflection=.12,Relative=False);mesh.write(str(out/(stem+'.stl')))
 check=Part.Shape();check.read(str(out/(stem+'.step')));assert check.isValid() and len(check.Solids)==1
 report['parts'][name]={'stem':stem,'quantity':quantity,'size_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength],'cad_solid_valid':True,'step_reimport_valid':True,'volume_mm3':shape.Volume,'supports_expected':support,'print_orientation':'rear side down; minimum Z set to zero' if orient=='rear' else 'front side down; minimum Z set to zero'}
 A.closeDocument(doc.Name)
export('speaker-shell',moved(body),16)
export('speaker-honeycomb-grille',moved(grille),16)
export('speaker-retaining-frame',moved(retainer),16)
for variant,centres in [('single-left',[-20]),('single-right',[20]),('twin',[-59,59])]:
 cover=original.copy()
 for cx in centres:cover=cover.fuse(moved(lid,cx))
 xmin=min(-27,min(centres)-25);xmax=max(27,max(centres)+25)
 cover=cover.fuse(box(xmin,-10,1,xmax-xmin,8,4))
 for x in [-23,23]:cover=cover.fuse(box(x-4,-6,1,8,10,2))
 for cx in centres:
  for dx in [-5,5]:cover=cover.cut(cyl(cx+dx,-3,0,1.5,7))
 # Reopen lid bores and nut seats after adding the bridge rail; it crosses
 # the inner top corner of each twin lid.
 for cx in centres:
  for x,y in mounts:
   cover=cover.cut(cyl(cx+x,y-37,0,1.7,8))
   rad=5.8/math.sqrt(3)
   pts=[V(cx+x+rad*math.cos(math.pi/3*i),y-37+rad*math.sin(math.pi/3*i),2.4) for i in range(6)]
   cover=cover.cut(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,5)))
 cover=cover.removeSplitter()
 assert original.cut(cover).Volume<1e-6
 assert cover.common(box(-250,0,-50,500,200,50)).Volume<1e-6
 for h in panelholes:
  x,y=h['xy'];assert cover.common(cyl(x,y,3.01,3.5,20)).Volume<1e-6
  assert cover.common(cyl(x,y,-1,1.99,10)).Volume<1e-6
 for cx in centres:
  for s in [body,grille,retainer,speaker,fibre]:assert cover.common(moved(s,cx)).Volume<1e-6,(variant,'collision')
  for x,y in mounts:assert cover.common(cyl(cx+x,y-37,0,1.69,8)).Volume<1e-6
 if len(centres)==2:
  a=moved(body,centres[0]);b=moved(body,centres[1]);assert a.distToShape(b)[0]>1.99
 export('speaker-T-cover-'+variant,cover,4,orient='rear',support=True)
 report['parts']['speaker-T-cover-'+variant]['original_T_preserved']=True
 report['parts']['speaker-T-cover-'+variant]['panel_holes_xy_mm']=[h['xy'] for h in panelholes]
 report['parts']['speaker-T-cover-'+variant]['speaker_centres_x_mm']=centres
# Assemblies with lightweight dimensional proxies, excluded from manufacturing exports.
for variant,centres in [('single-left',[-20]),('twin',[-59,59])]:
 doc=A.newDocument('Enclosure_'+variant.replace('-',''))
 def add(name,s,col):
  o=doc.addObject('PartDesign::Feature',name);o.Shape=s
  if o.ViewObject:o.ViewObject.ShapeColor=col
  return o
 add('Integrated_T_rear_cover',shapes['speaker-T-cover-'+variant],(.85,.85,.8))
 for i,cx in enumerate(centres):
  for n,s,c in [('Shell',body,(.9,.9,.86)),('Grille',grille,(.12,.12,.14)),('Retainer',retainer,(.3,.3,.3)),('Speaker_envelope_REFERENCE',speaker,(.15,.15,.17)),('Fibre_space_REFERENCE',fibre,(.7,.6,.4))]:add(n+str(i),moved(s,cx),c)
 doc.recompute();doc.saveAs(str(root/('Flockinator-enclosed-'+variant+'-assembly-v2.FCStd')))
 # Geometry-only preview assets; not printer parts.
 preview=root/'preview-meshes';preview.mkdir(exist_ok=True)
 for o in doc.Objects:
  if hasattr(o,'Shape'):MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.12,AngularDeflection=.2,Relative=False).write(str(preview/(variant+'-'+o.Name+'.stl')))
 A.closeDocument(doc.Name)
(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(report['parts']),'hex_holes':len(hexes),'status':'CAD assertions passed'},indent=2))
