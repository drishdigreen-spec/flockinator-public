"""Run inside FreeCAD through MCP. Dimensions in mm; concept, not print release."""
import FreeCAD as A
import FreeCADGui as G
import Part
import math
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
doc = A.newDocument('AcrylicNodeConcept')
groups = {}
def group(name):
    o = doc.addObject('App::DocumentObjectGroup', name)
    groups[name] = o
    return o
for name in ['Carrier', 'Lighting', 'Nodes', 'Frame', 'ExplodedNode']:
    group(name)

def box(x,y,z,w,h,d):
    return Part.makeBox(w,h,d,A.Vector(x,y,z))
def cyl(x,y,z,r,h):
    return Part.makeCylinder(r,h,A.Vector(x,y,z))
def add(name, shape, color, category, transparency=0):
    o=doc.addObject('Part::Feature',name)
    o.Shape=shape
    o.ViewObject.ShapeColor=color
    o.ViewObject.LineColor=(0.25,0.28,0.3)
    o.ViewObject.Transparency=transparency
    o.addProperty('App::PropertyString','Status')
    o.Status='Concept only: electronics, hole details, thermal/acoustic performance unverified'
    groups[category].addObject(o)
    return o
white=(0.91,0.92,0.89)
dark=(0.09,0.12,0.14)
teal=(0.12,0.7,0.68)
centres=[(-300+c*200,300-r*200) for r in range(4) for c in range(4)]
# Rounded acrylic carrier: 860 square, R30, thickness 6 is a trial value.
sheet=box(-400,-430,0,800,860,6).fuse(box(-430,-400,0,860,800,6))
for x in [-400,400]:
    for y in [-400,400]: sheet=sheet.fuse(cyl(x,y,0,30,6))
tools=[]
for x,y in centres:
    tools.append(box(x-52,y-56,-1,104,50,8))
    tools.append(box(x+48,y+22,-1,18,30,8))
    for dx in [-70,70]:
        for dy in [-70,70]: tools.append(cyl(x+dx,y+dy,-1,3,8))
mounts=[]
for t in [-200,200]:
    mounts.extend([(s,t) for s in [-18,18,-410,410]])
    mounts.extend([(t,s) for s in [-18,18,-410,410]])
tools.extend(cyl(x,y,-1,3,8) for x,y in mounts)
sheet=sheet.cut(Part.makeCompound(tools)).removeSplitter()
# 1.5 mm assembly seam; each tile has a 429.25 mm bounding envelope.
tiles=[]
for sx in [-1,1]:
    for sy in [-1,1]:
        x0=-430 if sx<0 else .75
        y0=-430 if sy<0 else .75
        shape=sheet.common(box(x0,y0,-1,429.25,429.25,8)).removeSplitter()
        tiles.append(add('Acrylic_tile_'+('Left' if sx<0 else 'Right')+('_Lower' if sy<0 else '_Upper'),shape,(0.64,0.85,0.93),'Carrier',65))
# Frame, not acrylic, takes handling and foot loads. Section is provisional.
for x in [-420,400]: add('Frame_upright',box(x,-420,-35,20,840,25),dark,'Frame')
for y in [-420,400]: add('Frame_crossmember',box(-400,y,-35,800,20,25),dark,'Frame')
# Provisional hollow aluminium cross, 20 face x 25 deep, 2 mm wall.
# Horizontal arms terminate at the continuous vertical member; joints TBD.
brace_shapes=[]
vbrace=box(-10,-400,-25,20,800,25).cut(box(-8,-401,-23,16,802,21))
brace_shapes.append(vbrace)
add('Aluminium_vertical_cross_brace_20x25x2_TRIAL',vbrace,(.68,.7,.73),'Frame')
for x0 in [-400,10]:
    shape=box(x0,-10,-25,390,20,25).cut(box(x0-1,-8,-23,392,16,21))
    brace_shapes.append(shape)
    add('Aluminium_horizontal_cross_arm_20x25x2_TRIAL',shape,(.68,.7,.73),'Frame')
# Wider saddle plates carry fasteners either side of the tile seams.
for t in [-200,200]:
    for vertical in [True,False]:
        plate=box(-30,t-20,-3,60,40,3) if vertical else box(t-20,-30,-3,40,60,3)
        holes=[cyl(s,t,-4,3,5) if vertical else cyl(t,s,-4,3,5) for s in [-18,18]]
        add('Tile_seam_saddle_plate_TRIAL',plate.cut(Part.makeCompound(holes)),(.68,.7,.73),'Frame')
# Short perimeter support pads bridge the previous frame-to-carrier depth gap.
for t in [-200,200]:
    for x,y in [(-410,t),(410,t),(t,-410),(t,410)]:
        add('Perimeter_tile_support_TRIAL',box(x-10,y-10,-10,20,20,10).cut(cyl(x,y,-11,3,12)),(.68,.7,.73),'Frame')
# Continuous rounded perimeter and merged T/cross junctions.
# Outer corner centreline R20, width 35.8 => outer R37.9 / inner R2.1.
def rounded_square(half,r,z,h):
    s=box(-half+r,-half,z,2*(half-r),2*half,h).fuse(box(-half,-half+r,z,2*half,2*(half-r),h))
    for x in [-half+r,half-r]:
        for y in [-half+r,half-r]: s=s.fuse(cyl(x,y,z,r,h))
    return s.removeSplitter()
def network(width,z,h):
    a=width/2
    s=rounded_square(400+a,20+a,z,h).cut(rounded_square(400-a,20-a,z-1,h+2))
    for v in [-200,0,200]:
        s=s.fuse(box(v-a,-400,z,width,800,h))
        s=s.fuse(box(-400,v-a,z,800,width,h))
    return s.removeSplitter()
add('Rounded_channel_network_REFERENCE',network(35.8,48,22).cut(network(29.8,51,22)).removeSplitter(),white,'Lighting')
add('Rounded_diffuser_network_REFERENCE',network(35.8,70,2),teal,'Lighting',20)
for v in [-400,-200,0,200,400]:
    for vertical in [True,False]:
        for t in [-300,-100,100,300]:
            px,py=(v,t) if vertical else (t,v)
            add('Channel_pedestal',box(px-6,py-6,6,12,12,42),white,'Lighting')

def node(x,y,category='Nodes',explode=False,index=0):
    # Module envelope 160 square. Peripheral shell, top/bottom vents, side ports.
    shell=box(-80,-80,18,160,160,45).cut(box(-77,-77,21,154,154,44))
    cuts=[box(-52,-56,17,104,50,6)]
    for vx in range(-60,65,20):
        cuts.extend([box(vx,-81,30,10,5,22),box(vx,76,30,10,5,22)])
    cuts.extend([box(76,18,31,6,18,12),box(76,44,31,6,18,12),box(-82,30,40,6,8,8)])
    shell=shell.cut(Part.makeCompound(cuts))
    # Local speaker chamber rear-facing; retain stock speaker housing.
    chamber=box(-58,-62,18,116,62,30).cut(box(-55,-59,17,110,56,28))
    speaker=box(-49.75,-53.4,23,99.5,44.8,21.3)
    grille=box(-55,-59,16,110,56,2)
    slots=[box(-49+q*14,-54,15,7,46,4) for q in range(7)]
    grille=grille.cut(Part.makeCompound(slots))
    items=[('Ventilated_node_tray',shell,white,0),('Rear_speaker_chamber',chamber,white,0),
           ('Speaker_body_REFERENCE',speaker,(0.23,0.24,0.25),0),('Rear_speaker_grille',grille,dark,0),
           ('Controller_REFERENCE',box(-48,15,24,76,48,12),(0.08,0.38,0.22),0),
           ('Five_mm_panel_riser_REFERENCE',box(-80,-80,63,160,160,5).cut(box(-77,-77,62,154,154,7)),white,0),
           ('Panel_REFERENCE',box(-80,-80,68,160,160,5),dark,0),
           ('Pixel_diffuser_REFERENCE',box(-80,-80,74,160,160,3),(0.25+index%3*.1,0.5,0.61),0)]
    for name,shape,color,trans in items:
        dz=0
        if explode:
            dz={'Rear_speaker_grille':-35,'Rear_speaker_chamber':0,'Speaker_body_REFERENCE':20,
                'Controller_REFERENCE':30,'Panel_REFERENCE':85,'Pixel_diffuser_REFERENCE':115}.get(name,0)
        shape.translate(A.Vector(x,y,dz))
        add(name,shape,color,category,trans)
    for dx in [-70,70]:
        for dy in [-70,70]:
            add('Mount_standoff_REFERENCE',cyl(x+dx,y+dy,6,5,12).cut(cyl(x+dx,y+dy,5,1.8,15)),(0.7,0.72,0.74),category)
    # Fine grid is a visual texture approximation, not a 64x64 baffle release.
    lines=[]
    facez=77 if not explode else 192
    for k in range(1,32):
        t=-80+k*5
        lines.extend([box(x+t,y-80,facez,.25,160,.12),box(x-80,y+t,facez,160,.25,.12)])
    add('Pixel_texture_ILLUSTRATIVE',Part.makeCompound(lines),(0.13,0.22,0.26),category)
for i,(x,y) in enumerate(centres): node(x,y,index=i)
node(0,0,'ExplodedNode',True)
for o in groups['ExplodedNode'].Group: o.ViewObject.Visibility=False
doc.recompute()
physical=[o for o in doc.Objects if hasattr(o,'Shape')]
invalid=[o.Name for o in physical if not o.Shape.isValid() or o.Shape.Volume<=0]
assert not invalid,invalid
doc.saveAs(str(OUT/'Flockinator-acrylic-node-concept.FCStd'))
G.activeDocument().activeView().viewAxonometric()
G.activeDocument().activeView().fitAll()
G.updateGui()
G.activeDocument().activeView().saveImage(str(OUT/'front-perspective.png'),1800,1400,'White')
G.activeDocument().activeView().viewBottom()
G.activeDocument().activeView().fitAll()
G.updateGui()
G.activeDocument().activeView().saveImage(str(OUT/'rear.png'),1800,1400,'White')
for category in ['Carrier','Lighting','Nodes','Frame']:
    for o in groups[category].Group: o.ViewObject.Visibility=False
for o in groups['ExplodedNode'].Group: o.ViewObject.Visibility=True
G.activeDocument().activeView().viewAxonometric()
G.activeDocument().activeView().fitAll()
G.updateGui()
G.activeDocument().activeView().saveImage(str(OUT/'exploded-node.png'),1600,1400,'White')
for o in groups['ExplodedNode'].Group: o.ViewObject.Visibility=False
for category in ['Carrier','Lighting','Nodes','Frame']:
    for o in groups[category].Group: o.ViewObject.Visibility=True
G.activeDocument().activeView().viewAxonometric()
G.activeDocument().activeView().fitAll()
doc.save()
(OUT/'validation.json').write_text(json.dumps({'valid_shape_objects':len(physical),'invalid':invalid,'print_ready':False,'pitch_mm':200,'acrylic_trial_mm':6,'panel_face_mm':160,'speaker_proxy_mm':[99.5,44.8,21.3],'outer_channel_radius_mm':37.9,'notes':['Shape validity only, not interference or engineering validation','Merged rounded channel network; production seams unresolved','Pixel texture is illustrative 32x32, not optical tooling','Electronics and connector positions are unmeasured proxies']},indent=2))
print('Saved concept and three previews:',OUT)
