"""Reimport delivered STEP parts, check joint neighbourhood and mount access."""
from pathlib import Path
import sys,json,itertools
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
V=App.Vector
root=Path(__file__).resolve().parent
report=json.loads((root/'validation.json').read_text())
def load(name):
    s=Part.Shape();s.read(str(root/'parts'/('Flockinator-'+name+'-v3.step')));return s
def placed(s,x=0,y=0,angle=0):
    s=s.copy();s.rotate(V(),V(0,0,1),angle);s.translate(V(x,y,0));return s
components={}
for side,x,y,a in [('top',80,0,0),('left',0,80,270)]:
    for name in ['straight-shell','straight-grille','speaker-retainer','straight-rear-cover']:components[side+'-'+name]=placed(load(name),x,y,a)
for name in ['corner-shell','corner-rear-cover']:components[name]=load(name)
for cy in [-20,-52]:
    components['topclip'+str(cy)]=placed(load('snap-bridge'),0,cy)
    components['leftclip'+str(cy)]=placed(load('snap-bridge'),cy,0,90)
checks=0
for (an,a),(bn,b) in itertools.combinations(components.items(),2):
    vol=a.common(b).Volume
    assert vol<1e-5,(an,bn,vol)
    checks+=1
# Space for a standard low head/washer at each shared panel screw.
for x,y in [(35,7),(7,35)]:
    bore=Part.makeCylinder(1.99,20,V(x,y,-2))
    access=Part.makeCylinder(3.5,10,V(x,y,6.31))
    for name,s in components.items():
        assert s.common(bore).Volume<1e-5,(name,'panel bore')
        assert s.common(access).Volume<1e-5,(name,'screw access')
report['checks']['reimported_step_corner_assembly']={'pair_checks':checks,'all_intersection_volumes_below_mm3':1e-5,'shared_panel_bores_clear':True,'shared_mount_7mm_head_access_clear':True}
(root/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['checks']['reimported_step_corner_assembly']))
