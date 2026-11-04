"""Run inside FreeCAD's bundled runtime. Concept geometry, not fitted hardware CAD."""
import FreeCAD as App
import Part, math, json
from pathlib import Path
ROOT = Path('/Volumes/devops/flockinator/cad/conductor-7inch')
p = json.loads((ROOT/'design-parameters.json').read_text())
W=p['housing_width_mm']; H=p['screen_plane_height_mm']; T=p['wall_mm']
a=p['angle_from_desk_deg']; rad=math.radians(a); D=H*math.cos(rad); F=p['front_shell_height_mm']
slope=math.tan(rad)
doc=App.newDocument('Conductor7Concept')
params=doc.addObject('Spreadsheet::Sheet','Parameters')
params.set('A1','CONCEPT ONLY - fit unverified')
for row,(key,val) in enumerate(p.items(),3):
    params.set('A'+str(row),key);params.set('B'+str(row),str(val))
params.setColumnWidth('A',260);params.setColumnWidth('B',420)
def wedge(x0,x1,y0,y1,z0,extra=0):
    pts=[App.Vector(x0,y0,z0),App.Vector(x0,y1,z0),App.Vector(x0,y1,F+slope*y1+extra),App.Vector(x0,y0,F+slope*y0+extra)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(x1-x0,0,0))
def inclined(shape):
    shape.rotate(App.Vector(0,0,0),App.Vector(1,0,0),a)
    shape.translate(App.Vector(0,0,F))
    return shape
results=[]
def add(name,shape,color,notes):
    shape=shape.removeSplitter()
    assert shape.isValid() and len(shape.Solids)==1, name
    obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
    obj.addProperty('App::PropertyString','FitStatus');obj.FitStatus=notes
    obj.ViewObject.ShapeColor=color
    results.append({'name':name,'valid':shape.isValid(),'solids':len(shape.Solids),'volume_mm3':shape.Volume,'bounds_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength]})
    return obj
# Open-topped wedge with a flat floor. No invented board mounting coordinates.
body=wedge(0,W,0,D,0).cut(wedge(T,W-T,T,D-T,T,10))
# Generic rear development access; not a registered connector cutout.
hatch_w=W-24; hatch_h=F+slope*D-22
body=body.cut(Part.makeBox(hatch_w,T+4,hatch_h,App.Vector(12,D-T-1,8)))
for x in (23,W-23):
    # Vent slots in front wall, remote from unverified hardware.
    for dx in range(0,24,6):
        body=body.cut(Part.makeBox(3,T+2,8,App.Vector(x+dx,-1,10)))
base=add('ConsoleShell',body,(0.16,0.19,0.23),'CONCEPT: no board mounts, no closure fasteners, unverified assembly clearance')
# Provisional speaker grille, leaving protective ribs in the front wall.
for offset in range(-18,19,6):
    body=body.cut(Part.makeBox(2,T+2,23,App.Vector(W/2+offset-1,-1,8)))
base.Shape=body.removeSplitter()
assert base.Shape.isValid() and len(base.Shape.Solids)==1
results[0]['volume_mm3']=base.Shape.Volume
# Screen-plane bezel with provisional centred opening.
ow=p['opening_width_mm'];oh=p['opening_height_mm'];bt=p['bezel_thickness_mm']
bezel=Part.makeBox(W,H,bt).cut(Part.makeBox(ow,oh,bt+2,App.Vector((W-ow)/2,(H-oh)/2,-1)))
front=add('ScreenBezel',inclined(bezel),(0.24,0.29,0.34),'CONCEPT: touch-glass outline/offset not measured; no display retention or screws')
# Rear plate is parked beside the case in the saved review view.
plate=Part.makeBox(hatch_w+10,T,hatch_h+10,App.Vector(W+15,0,0))
cover=add('RearServiceCover',plate,(0.21,0.25,0.29),'CONCEPT: shown detached; fasteners and fit lip pending')
# Bare LCD is a transparent reference only, not the real touch assembly.
lcd=Part.makeBox(165,100,3.5,App.Vector((W-165)/2,(H-100)/2,-3.5))
ref=add('BareLCDReference',inclined(lcd),(0.2,0.65,0.75),'REFERENCE ONLY: 165 x 100 x 3.5 bare LCD, excludes touch glass and adapter')
ref.ViewObject.Transparency=55
# Owner-specified speaker body envelope; no invented mounting-hole pattern.
# Body sits behind the front wall; long axis horizontal, cone provisionally forward.
speaker=add('SpeakerEnvelope',Part.makeBox(44,15,31,App.Vector((W-44)/2,T+1,T+1)),(0.75,0.45,0.2),'CLEARANCE ENVELOPE: 31 x 31 mm body; 44 mm overall across ears; 15 mm depth; 4 ohm, 3 W; 100 mm lead. Ear hole spacing/diameter and connector unverified')
speaker.ViewObject.Transparency=35
for obj in (base,front,cover):
    obj.ViewObject.LineColor=(0.08,0.09,0.11)
doc.recompute()
# Check assembly parts do not overlap; touching surfaces are intentional.
pairs=[]
for u,v in [(base,front),(base,ref),(front,ref),(base,speaker),(front,speaker),(ref,speaker)]:
    volume=u.Shape.common(v.Shape).Volume
    assert volume < 0.001, (u.Name,v.Name,volume)
    pairs.append({'parts':[u.Name,v.Name],'overlap_mm3':volume})
(ROOT/'concept-checks.json').write_text(json.dumps({'status':p['status'],'angle_from_desk_deg':a,'shell_footprint_mm':[W,D],'rear_shell_height_mm':F+slope*D,'parts':results,'intersections':pairs,'limitations':['No fitted board or touch assembly','No closure or hardware retention','No registered ports','Not print-ready']},indent=2))
doc.saveAs(str(ROOT/'Conductor-7inch-concept.FCStd'))
Part.export([base,front,cover,ref,speaker],str(ROOT/'Conductor-7inch-concept.STEP'))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
Gui.activeDocument().activeView().saveImage(str(ROOT/'concept-preview.png'),1400,1000,'White')
print(json.dumps({'saved':str(ROOT/'Conductor-7inch-concept.FCStd'),'checks':results,'overlaps':pairs}))
