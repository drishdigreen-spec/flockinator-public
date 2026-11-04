"""uv run --with trimesh --with scipy --with networkx --with matplotlib render_preview.py"""
from pathlib import Path
import json,numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
p=Path(__file__).resolve().parent;m=trimesh.load(p/'Flockinator-X-joint-fit-test.stl');r=json.loads((p/'validation.json').read_text())
assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
r['STL']={'watertight':bool(m.is_watertight),'consistent_winding':bool(m.is_winding_consistent),'connected_bodies':1,'triangles':len(m.faces),'volume_mm3':float(m.volume)}
(p/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
f=plt.figure(figsize=(13,6),facecolor='#f5f5f2')
a=f.add_subplot(121,projection='3d');colors=np.clip(.68+.23*m.face_normals@np.array([.2,-.3,.9]),.4,.93);rgba=np.column_stack([colors*.94,colors*.97,colors,np.ones(len(colors))]);a.add_collection3d(Poly3DCollection(m.triangles,facecolors=rgba,edgecolor='none'))
a.set(xlim=(-43,43),ylim=(-43,43),zlim=(0,12));a.set_box_aspect([86,86,20]);a.view_init(45,-60);a.set_axis_off();a.set_title('Four-way rear connector',fontsize=16,pad=12)
b=f.add_subplot(122);b.set_facecolor('#eeeeea')
sec=m.section(plane_origin=[0,0,1],plane_normal=[0,0,1])
loops=sorted(sec.discrete,key=len,reverse=True)
# Largest bounding extent is the outside perimeter.
loops.sort(key=lambda d:np.prod(np.ptp(d[:,:2],axis=0)),reverse=True)
b.fill(loops[0][:,0],loops[0][:,1],color='#c1cbd5',edgecolor='#394d60',linewidth=1.4)
for x,y in r['hole_centres_mm']:b.add_patch(Circle((x,y),2,color='#f5f5f2',ec='#394d60',lw=1))
b.axhline(0,color='#75818a',ls='--',lw=.8);b.axvline(0,color='#75818a',ls='--',lw=.8)
for sign in [-1,1]:
 b.plot([0,20*sign],[0,20*sign],color='#718296',lw=3)
 b.plot([0,20*sign],[0,-20*sign],color='#718296',lw=3)
b.annotate('',xy=(-10,44),xytext=(10,44),arrowprops={'arrowstyle':'<->','color':'#243649'})
b.text(0,46,'20 mm centres',ha='center',fontsize=10)
b.annotate('',xy=(44,0),xytext=(44,33),arrowprops={'arrowstyle':'<->','color':'#243649'})
b.text(47,16.5,'33 mm',rotation=90,va='center',fontsize=10)
b.set(xlim=(-47,54),ylim=(-44,53),xlabel='mm',ylabel='mm');b.set_aspect('equal');b.set_title('Hole positions to confirm',fontsize=16,pad=12)
f.suptitle('Flockinator temporary X joint | FIT TEST CANDIDATE',fontsize=18,y=.98)
f.text(.5,.025,'78 × 78 mm envelope · 3 mm plate + 3 mm rear ribs · 8 clearance holes · touching panels',ha='center',fontsize=11)
f.subplots_adjust(top=.83,bottom=.13,wspace=.13);f.savefig(p/'preview.png',dpi=170)
print(r['STL'])
