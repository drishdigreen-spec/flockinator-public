"""Run with FreeCAD's bundled Python; no GUI process or safe-mode launch."""
import sys,json
from pathlib import Path
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App, Part
root=Path(__file__).resolve().parent
cfg=json.loads((root/'assembly.json').read_text())
doc=App.newDocument('FlockinatorPresentation')
groups=[]
for n in cfg['group_names']:
    groups.append(doc.addObject('App::DocumentObjectGroup',n))
objects=[]
for p in cfg['parts']:
    o=doc.addObject('Part::Feature',p['name']);x,y,z=p['center'];w,h,d=p['size']
    if 'outline' in p:
        def face(points):
            vectors=[App.Vector(x+a,y+b,z-d/2) for a,b in points]
            return Part.Face(Part.makePolygon(vectors+[vectors[0]]))
        profile=face(p['outline'])
        for hole in p['holes']:profile=profile.cut(face(hole))
        o.Shape=profile.extrude(App.Vector(0,0,d))
    else:o.Shape=Part.makeBox(w,h,d,App.Vector(x-w/2,y-h/2,z-d/2))
    o.addProperty('App::PropertyString','Role');o.Role=p['role']
    o.addProperty('App::PropertyString','Status');o.Status='Concept envelope; verify interfaces before printing'
    groups[p['module']].addObject(o);objects.append(o)
# All 4096 compartments per panel, nominal pitch; LED registration unverified.
for r in range(4):
    for c in range(4):
        x=-300+c*200;y=300-r*200;pieces=[]
        for k in range(1,64):
            t=-80+k*2.5
            pieces.append(Part.makeBox(.4,160,2.4,App.Vector(x+t-.2,y-80,72.6)))
            pieces.append(Part.makeBox(160,.4,2.4,App.Vector(x-80,y+t-.2,72.6)))
        for t in [-80,79.8]:
            pieces.append(Part.makeBox(.2,160,2.4,App.Vector(x+t,y-80,72.6)))
            pieces.append(Part.makeBox(160,.2,2.4,App.Vector(x-80,y+t,72.6)))
        o=doc.addObject('Part::Feature',f'PixelBaffles_{r*4+c+1:02d}')
        o.Shape=Part.makeCompound(pieces)
        o.addProperty('App::PropertyString','Status');o.Status='64 x 64 optical compartments; overlapping strip solids, not fused print release'
        groups[1].addObject(o)
s=doc.addObject('Spreadsheet::Sheet','DesignParameters')
for row,(k,v) in enumerate([('STATUS','PRESENTATION CONCEPT - NOT PRINT RELEASE'),('Pitch mm',200),('Panel mm',160),('Pixels per node',4096),('Backing width mm',875.8),('Track outer corner radius mm',35.8),('Backing corner radius mm',45),('Depth incl rear power box mm',257.8),('Foot depth mm',500),('Height incl feet mm',915.8),('Display height mm - remote separate',875.8),('Channel face Z mm',75.8),('Panel face Z mm',75.4)],1):
    s.set(f'A{row}',str(k));s.set(f'B{row}',str(v))
doc.recompute()
invalid=[o.Name for o in objects if not o.Shape.isValid()]
assert not invalid,invalid
out=root/'Flockinator-presentation.FCStd';doc.saveAs(str(out))
Part.export(objects,str(root/'Flockinator-presentation.step'))
(root/'cad-validation.json').write_text(json.dumps({'envelope_objects':len(objects),'invalid_envelopes':invalid,'panels':16,'pixels_per_node':4096,'optical_grids':16,'groups':4,'print_ready':False,'notes':['Channel bodies are solid envelopes, not hollow printable tracks','Pixel grids are compounds with overlapping strip solids','Rigid structure and mounting capacity unverified; handheld remote dimensions provisional']},indent=2))
print('SAVED',out)
