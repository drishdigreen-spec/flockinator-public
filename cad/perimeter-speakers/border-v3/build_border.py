"""Flockinator independent continuous enclosure prototype, GPL-3.0-or-later.
Assembly axes: +Y inward from top panel edge, +Z rearward, millimetres.
Run with bundled FreeCAD Python. No GUI or safe mode required.
"""
from pathlib import Path
import sys, math, json
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, MeshPart
V = App.Vector
ROOT = Path(__file__).resolve().parent
for folder in ['parts', 'preview-meshes']:
    (ROOT / folder).mkdir(exist_ok=True)

def box(x,y,z,w,h,d): return Part.makeBox(w,h,d,V(x,y,z))
def cylinder(x,y,z,r,h): return Part.makeCylinder(r,h,V(x,y,z))
def shift(s,x=0,y=0,z=0):
    s=s.copy(); s.translate(V(x,y,z)); return s

def rounded(w,h,r,z,d,cx=0,cy=0):
    s=box(-w/2+r,-h/2,z,w-2*r,h,d).fuse(box(-w/2,-h/2+r,z,w,h-2*r,d))
    for x in [-w/2+r,w/2-r]:
        for y in [-h/2+r,h/2-r]: s=s.fuse(cylinder(x,y,z,r,d))
    return shift(s.removeSplitter(),cx,cy)

def capsule(a,b,r,z,d):
    dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
    bar=box(0,-r,z,length,2*r,d)
    bar.rotate(V(0,0,0),V(0,0,1),math.degrees(math.atan2(dy,dx)))
    bar.translate(V(a[0],a[1],0))
    return bar.fuse(cylinder(*a,z,r,d)).fuse(cylinder(*b,z,r,d))

def nut(x,y,z,h):
    r=5.8/math.sqrt(3)
    pts=[V(x+r*math.cos(i*math.pi/3),y+r*math.sin(i*math.pi/3),z) for i in range(6)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,h))

def bore(s, holes, z=-40,h=60, nuts=False):
    for x,y in holes:
        s=s.cut(cylinder(x,y,z,1.7,h))
        if nuts: s=s.cut(nut(x,y,.4,10))
    return s.removeSplitter()

def post(x,y):
    return cylinder(x,y,3,2,3).fuse(Part.makeCone(2,3,1,V(x,y,6))).fuse(cylinder(x,y,7,3,.3))

MOUNTS=[(x,-36+y) for x in [-55,55] for y in [-28,28]]
EDGE=[(-45,7),(45,7)]
POSTS=[(x,y) for x in [-75,75] for y in [-20,-52]]
body=box(-79.8,-70,-32,159.6,68,31)
body=body.cut(rounded(104,50,4,-30,31,cy=-36)).cut(rounded(94,40,3,-33,4,cy=-36))
# Closed side bays save material while central partitions isolate each speaker.
for x in [-76.8,58]:
    bay=box(x,-67,-30,18.8,62,30)
    for hx,hy in MOUNTS: bay=bay.cut(cylinder(hx,hy,-31,4.5,33))
    body=body.cut(bay)
# Cable channel at the inner rear seam, from acoustic chamber to outside.
body=body.cut(box(-3,-12,-4,6,11,4)); body=bore(body,MOUNTS)
grille=box(-79.8,-70,-35,159.6,68,3)
window=rounded(94,40,3,-36,5,cy=-36)
hexes=[]
for row in range(-4,5):
    for col in range(-9,10):
        cx=math.sqrt(3)*4.5*(col+.5*(row%2)); cy=-36+6.75*row
        pts=[V(cx+3.7*math.cos(math.radians(30+60*i)),cy+3.7*math.sin(math.radians(30+60*i)),-36) for i in range(6)]
        h=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,5))
        if h.cut(window).Volume<1e-7: hexes.append(h)
grille=grille.cut(Part.makeCompound(hexes))
grille=grille.fuse(box(79.8,-70,-35,4.2,68,1.5)).cut(box(-80,-70,-35.1,4.4,68,1.9))
grille=bore(grille,MOUNTS)
retainer=rounded(102,48,2,-6,2.5,cy=-36).cut(rounded(90,36,2,-7,5,cy=-36)).removeSplitter()
cover=box(-79.8,-70,-1,159.6,68,4)
for x in [-48,48]:
    for y in [-57,-15]: cover=cover.fuse(box(x-2,y-2,-3.5,4,4,2.5))
for x,y in EDGE: cover=cover.fuse(capsule((x,-6),(x,y),6,0,3))
for x,y in POSTS: cover=cover.fuse(post(x,y))
for x,y in EDGE: cover=cover.cut(cylinder(x,y,-1,2,8))
# Pair of cable-tie holes outside the acoustic box, in inner lip.
for x in [-8,8]: cover=cover.cut(cylinder(x,-4,-2,1.4,6))
cover=bore(cover,MOUNTS,nuts=True)
speaker=rounded(99.5,44.8,2,-29,21.3,cy=-36)
fibre=box(-40,-49,-6.5,80,26,5)

# Canonical top-left corner with R20 outside and a 2 mm panel gap.
def corner_outline(inset,z,d):
    lo=-70+inset; hi=-inset; c=-50; r=20-inset
    s=box(c,lo,z,hi-c,hi-lo,d).fuse(box(lo,c,z,hi-lo,hi-c,d))
    q=cylinder(c,c,z,r,d).common(box(lo,lo,z,r,r,d))
    return s.fuse(q).removeSplitter()
CORNER_MOUNTS=[(-57,-57),(-57,-14),(-14,-57),(-25,-10)]
corner=corner_outline(0,-35,34).cut(corner_outline(3,-32,32))
for x,y in CORNER_MOUNTS: corner=corner.fuse(cylinder(x,y,-35,4.5,34))
# Inner corner stop: no solid overlaps the panel quadrant.
corner=corner.cut(box(-2,-2,-36,3,3,40))
corner=corner.fuse(box(0,-70,-35,4,68,1.5))
corner=corner.cut(box(-70,-4.4,-35.1,68,4.5,1.9))
corner=bore(corner,CORNER_MOUNTS)
corner_cover=corner_outline(0,-1,4).cut(box(-2,-2,-2,3,3,6))
CORNER_POSTS=[(-5,-20),(-5,-52),(-20,-5),(-52,-5)]
for x,y in CORNER_POSTS: corner_cover=corner_cover.fuse(post(x,y))
# Raised rear brace shares two nearby panel-edge screws with straight tabs.
corner_cover=corner_cover.fuse(cylinder(-33,-33,3,6,3.3))
for a,b in [((-33,-33),(4,4)),((4,4),(35,7)),((4,4),(7,35))]:
    corner_cover=corner_cover.fuse(capsule(a,b,4,3.3,3))
for x,y in [(35,7),(7,35)]:
    corner_cover=corner_cover.fuse(cylinder(x,y,3,6,3.3)).cut(cylinder(x,y,-1,2,12))
corner_cover=bore(corner_cover,CORNER_MOUNTS,nuts=True)

# Two open C sockets snap sideways onto paired mushroom posts. Actual snap fit
# is deliberately a coupon test: static clearance cannot prove PLA flexure.
def clip(throat):
    s=capsule((-5,0),(5,0),4,3.2,2.4)
    for x in [-5,5]:
        s=s.cut(cylinder(x,0,3,2.2,3))
        s=s.cut(box(x-throat/2,0,3,throat,5,3))
    return s.removeSplitter()
clip_standard=clip(3.2); clip_loose=clip(3.6)
coupon=box(-11,-7,0,22,14,3)
for x in [-5,5]: coupon=coupon.fuse(post(x,0))
coupon=coupon.removeSplitter()
spacers={f'spacer-{height}mm':cylinder(0,0,0,5,height).cut(cylinder(0,0,-1,2,height+2)) for height in [1,2]}

SHAPES={'straight-shell':body,'straight-grille':grille,'speaker-retainer':retainer,'straight-rear-cover':cover,'corner-shell':corner,'corner-rear-cover':corner_cover,'snap-bridge':clip_standard,'snap-bridge-loose':clip_loose,'snap-test-posts':coupon,**spacers}
QUANTITIES={'straight-shell':16,'straight-grille':16,'speaker-retainer':16,'straight-rear-cover':16,'corner-shell':4,'corner-rear-cover':4,'snap-bridge':40,'snap-bridge-loose':0,'snap-test-posts':1,'spacer-1mm':0,'spacer-2mm':0}
report={'status':'Geometric prototype, not sliced or physically fitted','outer_envelope_mm':[780,780],'panel_array_mm':[640,640],'centres_per_side_mm':[80,240,400,560],'straight_pitch_mm':160,'body_joint_gap_mm':.4,'lap_depth_clearance_mm':.3,'max_printed_rear_z_mm':7.3,'rear_mount_seat_depth':'unknown; spacer selection requires measurement','hex_holes_per_speaker':len(hexes),'speaker_reference_envelope_mm':[99.5,44.8,21.3],'fibre_reservation_mm':[80,26,5],'parts':{},'checks':{}}

def ensure_clear(a,b,name):
    vol=a.common(b).Volume
    assert vol<1e-6,(name,vol)
    report['checks'][name]={'intersection_mm3':vol}
for name,s in [('shell',body),('grille',grille),('retainer',retainer),('cover',cover)]:
    ensure_clear(s,speaker,name+'_speaker')
    ensure_clear(s,fibre,name+'_fibre')
parts=[body,grille,retainer,cover]
for i,a in enumerate(parts):
    for j,b in enumerate(parts[:i]): ensure_clear(a,b,f'module_parts_{i}_{j}')
ensure_clear(corner,corner_cover,'corner_shell_cover')
# Exact corner neighbourhood: first top module centred (80,0), last left centred (0,80).
def rotated(s,angle,x=0,y=0):
    s=s.copy();s.rotate(V(0,0,0),V(0,0,1),angle);s.translate(V(x,y,0));return s
for name,s in [('shell',body),('grille',grille),('cover',cover)]:
    ensure_clear(s,shift(s,160),name+'_adjacent_identical')
# Cross-part checks at straight joint, plus corner neighbourhood.
for i,a in enumerate(parts):
    for j,b in enumerate(parts): ensure_clear(a,shift(b,160),f'adjacent_{i}_{j}')
for side,angle,x,y in [('top',0,80,0),('left',270,0,80)]:
    for cn,c in [('shell',corner),('cover',corner_cover)]:
        for sn,s in [('shell',body),('grille',grille),('retainer',retainer),('cover',cover)]:
            ensure_clear(c,rotated(s,angle,x,y),f'corner_{cn}_{side}_{sn}')
for throat,c in [('standard',clip_standard),('loose',clip_loose)]:
    ensure_clear(c,coupon,'clip_coupon_'+throat)
# Seated connectors at straight seam; two rear bridge clips.
for y in [-20,-52]:
    c=shift(clip_standard,80,y)
    ensure_clear(c,cover,'clip_left_'+str(y));ensure_clear(c,shift(cover,160),'clip_right_'+str(y))
for x,y in EDGE:
    ensure_clear(cover,cylinder(x,y,-2,1.99,15),'edge_bore_'+str(x))
# Panel quadrant is unobstructed forward of its rear face.
ensure_clear(cover,box(-80,0,-40,160,160,40),'no_panel_front_intrusion_straight')
ensure_clear(corner_cover,box(0,0,-40,160,160,40),'no_panel_front_intrusion_corner')

for name,s in SHAPES.items():
    s=s.removeSplitter();SHAPES[name]=s
    assert s.isValid() and len(s.Solids)==1,(name,s.isValid(),len(s.Solids))
    doc=App.newDocument('part_'+name.replace('-','_'));o=doc.addObject('PartDesign::Feature','Solid');o.Shape=s;o.Label=name
    for prop,val in [('Status',report['status']),('PrintSettings','50% gyroid; 5 wall loops'),('MountReference','P2.5 DWG: ±45 / +7 edge M3 coordinates')]:
        o.addProperty('App::PropertyString',prop);setattr(o,prop,val)
    doc.recompute();stem='Flockinator-'+name+'-v3';doc.saveAs(str(ROOT/'parts'/(stem+'.FCStd')));Part.export([o],str(ROOT/'parts'/(stem+'.step')))
    p=s.copy();p.translate(V(0,0,-p.BoundBox.ZMin))
    MeshPart.meshFromShape(Shape=p,LinearDeflection=.04,AngularDeflection=.12,Relative=False).write(str(ROOT/'parts'/(stem+'.stl')))
    check=Part.Shape();check.read(str(ROOT/'parts'/(stem+'.step')))
    assert check.isValid() and len(check.Solids)==1
    report['parts'][name]={'stem':stem,'full_array_quantity':QUANTITIES[name],'size_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength],'volume_mm3':s.Volume,'cad_valid_single_solid':True,'step_reimport_valid':True,'orientation':'Front/down as assembled, translated to bed; review supports','supports_expected':name in ['straight-grille','straight-rear-cover','corner-shell','corner-rear-cover']}
    MeshPart.meshFromShape(Shape=s,LinearDeflection=.12,AngularDeflection=.2,Relative=False).write(str(ROOT/'preview-meshes'/(name+'.stl')))
    App.closeDocument(doc.Name)
for name,s in [('speaker-REFERENCE',speaker),('fibre-REFERENCE',fibre)]:
    MeshPart.meshFromShape(Shape=s,LinearDeflection=.12,AngularDeflection=.2,Relative=False).write(str(ROOT/'preview-meshes'/(name+'.stl')))

# Complete assembly uses linked definitions for compact editable placement.
doc=App.newDocument('Flockinator_border_v3')
definitions={}
for name,s in SHAPES.items():
    obj=doc.addObject('PartDesign::Feature','Definition_'+name.replace('-','_'));obj.Shape=s;obj.Label='Definition: '+name;definitions[name]=obj
    if obj.ViewObject:obj.ViewObject.Visibility=False
placements=[(0,0,0),(90,640,0),(180,640,640),(270,0,640)]
for side,(angle,tx,ty) in enumerate(placements):
    for k in range(4):
        for name in ['straight-shell','straight-grille','speaker-retainer','straight-rear-cover']:
            obj=doc.addObject('App::Link',f'Side{side}_Node{k}_{name.replace("-","_")}');obj.setLink(definitions[name])
            transform=App.Placement(V(tx,ty,0),App.Rotation(V(0,0,1),angle)).multiply(App.Placement(V(80+160*k,0,0),App.Rotation()))
            obj.Placement=transform
    for name in ['corner-shell','corner-rear-cover']:
        obj=doc.addObject('App::Link',f'Corner{side}_{name.replace("-","_")}');obj.setLink(definitions[name]);obj.Placement=App.Placement(V(tx,ty,0),App.Rotation(V(0,0,1),angle))
    # Five joints per side: corner-to-straights and last straight-to-next corner.
    for seam in range(5):
        for y in [-20,-52]:
            obj=doc.addObject('App::Link',f'Clip_{side}_{seam}_{abs(y)}');obj.setLink(definitions['snap-bridge'])
            obj.Placement=App.Placement(V(tx,ty,0),App.Rotation(V(0,0,1),angle)).multiply(App.Placement(V(seam*160,y,0),App.Rotation()))
# Reference panels are simple envelopes, no invented detailed panel/PCB mechanics.
for row in range(4):
    for col in range(4):
        obj=doc.addObject('PartDesign::Feature',f'Panel_{chr(65+row)}{col+1}_REFERENCE');obj.Shape=box(col*160+.1,row*160+.1,-10,159.8,159.8,10)
        if obj.ViewObject:obj.ViewObject.ShapeColor=(.10,.12,.14)
doc.recompute();doc.saveAs(str(ROOT/'Flockinator-continuous-border-v3.FCStd'));App.closeDocument(doc.Name)
(ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(SHAPES),'checks':len(report['checks']),'status':'CAD checks passed'}))
