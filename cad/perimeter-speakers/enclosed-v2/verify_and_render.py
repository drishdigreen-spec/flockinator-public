from pathlib import Path
import json,math,itertools,zipfile
import trimesh,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
root=Path(__file__).resolve().parent;r=json.loads((root/'validation.json').read_text())
for name,p in r['parts'].items():
 m=trimesh.load(root/'parts'/(p['stem']+'.stl'));assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,name
 assert abs(m.bounds[0,2])<1e-5
 bores={}
 if 'T-cover' in name:
  m.apply_translation([0,0,-6]);m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]));height=2
  expected=[(x,y,4) for x,y in p['panel_holes_xy_mm']]+[(cx+x,-37+y,3.4) for cx in p['speaker_centres_x_mm'] for x in [-53,53] for y in [-26,26]]
 elif name in ['speaker-shell','speaker-honeycomb-grille']:
  height=15 if name=='speaker-shell' else 1.5;expected=[(x,y-37,3.4) for x in [-53,53] for y in [-26,26]]
 else:expected=[]
 if expected:
  sec=m.section(plane_origin=[0,0,height],plane_normal=[0,0,1]);found=[]
  for loop in sec.discrete:
   ext=np.ptp(loop[:,:2],axis=0)
   for diam in [3.4,4]:
    if np.allclose(ext,[diam,diam],atol=.025):
     x,y=loop[:-1,0],loop[:-1,1];fit=np.linalg.lstsq(np.column_stack([2*x,2*y,np.ones(len(x))]),x*x+y*y,rcond=None)[0];found.append((fit[0],fit[1],diam))
  errs=[min(math.hypot(x-u,y-v) for u,v,d in found if d==diam) for x,y,diam in expected];assert max(errs)<.01,(name,errs)
  bores={'verified_bores':len(expected),'max_centre_error_mm':max(errs)}
 p['STL_checks']={'watertight':True,'consistent_winding':True,'one_connected_body':True,'bed_min_z_mm':0,**bores}
# Numeric layout, with each side rotated clockwise from top.
slots=[140,261,379,500];assert all(b-a-116>=2 for a,b in zip(slots,slots[1:]))
r['array_case_envelope_mm']=[776,776];r['edge_speaker_centres_mm']=slots
(root/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
# Render with a per-pixel depth buffer to resolve adjoining CAD surfaces.
import runpy
runpy.run_path(str(root/'render_depth.py'))
# Clear side-section diagram: actual shell cut by X=0, plus annotated envelopes.
fig,ax=plt.subplots(figsize=(11,5),facecolor='white')
from matplotlib.patches import Rectangle
ax.add_patch(Rectangle((-35,-68),40,62,fc='#e6e5dc',ec='#454e52'))
ax.add_patch(Rectangle((-30,-62),31,50,fc='white',ec='#777'))
ax.add_patch(Rectangle((-29,-59.4),21.3,44.8,fc='#4d555a',ec='black'))
ax.add_patch(Rectangle((-4.5,-50),5,26,fc='#cbbd9c',ec='#776b55',hatch='...'))
ax.plot([12,12],[-76,10],color='#44809b',lw=3);ax.text(13,-40,'Whiteboard\nassumed Z = +12',va='center',fontsize=10)
ax.annotate('',xy=(5,-73),xytext=(12,-73),arrowprops={'arrowstyle':'<->'});ax.text(8.5,-77,'7 mm nominal',ha='center',fontsize=9)
ax.annotate('Speaker envelope',xy=(-17,-42),xytext=(-31,-15),arrowprops={'arrowstyle':'->'})
ax.annotate('Loose fibre space',xy=(-2,-41),xytext=(17,-18),arrowprops={'arrowstyle':'->'})
ax.text(-35,-83,'Front / audience',fontsize=10);ax.text(-3,-83,'Rear',fontsize=10)
ax.set_xlim(-42,45);ax.set_ylim(-87,8);ax.set_aspect('equal');ax.axis('off');fig.suptitle('Depth arrangement · schematic envelopes, dimensions in mm',fontsize=15)
fig.text(.5,.025,'Small intentional grille holes, retainers, bolts and cable exit omitted from this depth diagram. Verify installed clearance.',ha='center',fontsize=9)
fig.savefig(root/'depth-clearance.png',dpi=140)
print(json.dumps({n:p['STL_checks'] for n,p in r['parts'].items()},indent=2))
