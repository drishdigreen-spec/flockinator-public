"""Run with FreeCAD's own runtime. Geometric study, not fabrication drawings."""
import FreeCAD as App
import Part, Mesh, math, os, json
ROOT='/Volumes/devops/flockinator'
BASE=ROOT+'/references/duality-track-system-bundle-original-track-and-evolution-pack-model_files'
doc=App.newDocument('FlockinatorGridFit')
cache={}
def group(name,label):
    o=doc.addObject('App::DocumentObjectGroup',name);o.Label=label;return o
tracks=group('Tracks','Purchased track meshes - 250 mm pitch')
skins=group('Diffusers','Purchased seamless MatteHex covers')
panels=group('Panels','16 panel envelopes - 160 x 160 mm')
gaps=group('Adaptations','12 short spans - adaptation required')
rear=group('RearSpace','Concealed hardware space - provisional')
def mesh(name,file,center,angle,x,y,parent):
    if file not in cache:cache[file]=Mesh.Mesh(BASE+'/'+file)
    m=cache[file].copy();a=math.radians(angle);c=math.cos(a);s=math.sin(a)
    t=App.Matrix();t.A11=c;t.A12=0;t.A13=-s;t.A21=s;t.A22=0;t.A23=c;t.A31=0;t.A32=1;t.A33=0
    t.A14=x-c*center[0]+s*center[1];t.A24=y-s*center[0]-c*center[1]
    m.transform(t);m.flipNormals()
    o=doc.addObject('Mesh::Feature',name);o.Mesh=m;parent.addObject(o)
    o.addProperty('App::PropertyString','SourceFile');o.SourceFile=file
    return o
def box(name,x,y,z,w,h,d,parent,label):
    o=doc.addObject('Part::Feature',name);o.Shape=Part.makeBox(w,h,d,App.Vector(x,y,z));o.Label=label
    if parent:parent.addObject(o)
    return o
P=250.0
# Tee stem points inward; source tee intersection is at (0,-7.1),
# with 75 mm side arms and a 132.1 mm stem. Skin is rotated relative to track.
for r in range(5):
    for c in range(5):
        x=c*P;y=r*P;name='J_%d_%d'%(r,c)
        if r in (0,4) and c in (0,4):
            # Source corner arms point -X and +Y.
            a={(0,0):-90,(0,4):0,(4,0):180,(4,4):90}[(r,c)]
            mesh(name,'track_90_150.stl',(0,50),a,x,y,tracks)
            mesh('Skin_'+name,'SeamlessMatteHex/skin_mattehex_90_150_lh.stl',(0,50),a,x,y,skins)
        elif r in (0,4) or c in (0,4):
            a=0 if r==0 else 180 if r==4 else -90 if c==0 else 90
            mesh(name,'track_tee_150.stl',(0,-7.1),a,x,y,tracks)
            mesh('Skin_'+name,'SeamlessMatteHex/skin_mattehex_tee_150.stl',(0,-7.1),a+90,x,y,skins)
        else:
            mesh(name,'track_cross_150.stl',(0,50),0,x,y,tracks)
            mesh('Skin_'+name,'SeamlessMatteHex/skin_mattehex_cross_150.stl',(0,50),0,x,y,skins)
def arm(r,c,dr,dc):
    return 132.1 if ((r==0 and dr==1) or (r==4 and dr==-1) or (c==0 and dc==1) or (c==4 and dc==-1)) and not (r in (0,4) and c in (0,4)) else 75.0
for r in range(5):
    for c in range(5):
        for dr,dc in ((0,1),(1,0)):
            rr=r+dr;cc=c+dc
            if rr>4 or cc>4:continue
            start=arm(r,c,dr,dc);end=arm(rr,cc,-dr,-dc);length=P-start-end
            x=c*P+dc*start;y=r*P+dr*start;name='Span_%d_%d_%d_%d'%(r,c,rr,cc)
            if abs(length-100)<.01:
                mesh(name,'track_straight_100.stl',(0,25),-90 if dc else 0,x,y,tracks)
                mesh('Skin_'+name,'SeamlessMatteHex/skin_mattehex_straight_100.stl',(0,25),-90 if dc else 0,x,y,skins)
            else:
                box(name,x if dc else x-17.9,y-17.9 if dc else y,0,length if dc else 35.8,35.8 if dc else length,23.3,gaps,'ADAPTATION %.1f mm span'%length)
for r in range(4):
    for c in range(4):
        x=(c+.5)*P;y=(r+.5)*P
        o=box('Node_%02d'%(r*4+c+1),x-80,y-80,48,160,160,6,panels,'Node %02d - face envelope, depth provisional'%(r*4+c+1))
        o.addProperty('App::PropertyString','ValidationNote');o.ValidationNote='160 mm face confirmed; thickness and M3 positions unverified'
        box('HiddenVolume_%02d'%(r*4+c+1),x-70,y-70,0,140,140,45,rear,'Reserved rear volume - not verified hardware dimensions')
back=box('Backing',-37.9,-37.9,-6,1075.8,1075.8,6,None,'Backing envelope - 6 mm trial thickness, material undecided')
params=doc.addObject('Spreadsheet::Sheet','Dimensions')
for cell,value in {'A1':'Geometric study, not fabrication-ready','A2':'Grid pitch mm','B2':'250','A3':'Panel face mm','B3':'160','A4':'Nominal clear opening mm','B4':'214.2','A5':'Short span mm','B5':'42.9','A6':'Panel rear plane mm (trial)','B6':'48','A7':'Compact target pitch mm','B7':'185.8','A8':'Compact clear opening mm','B8':'150'}.items():params.set(cell,value)
doc.recompute()
os.makedirs(ROOT+'/cad',exist_ok=True)
doc.saveAs(ROOT+'/cad/Flockinator-grid-fit.FCStd')
report={'pitch_mm':250,'panel_face_mm':160,'nominal_opening_mm':214.2,'panel_clearance_per_side_mm':27.1,'panel_edge_gap_mm':90,'short_span_mm':42.9,'counts':{'crosses':9,'tees':12,'corners':4,'stock_100mm_straights':28,'adaptation_spans':12},'panel_overlap_area_mm2':0,'status':'Face fit only; mount holes, depth, couplers and seam phase unverified'}
with open(ROOT+'/cad/fit-report.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
