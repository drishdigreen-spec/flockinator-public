from pathlib import Path
import json,math
import trimesh,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
root=Path(__file__).resolve().parent;r=json.loads((root/'carrier-validation.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(16,6),facecolor='white')
for ax,(variant,part) in zip(axes,r['parts'].items()):
 m=trimesh.load(root/'carriers-v1'/(part['stem']+'.stl'))
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 assert abs(m.bounds[0,2])<1e-4
 # Back to assembly coordinates for actual mesh sections.
 m.apply_translation([0,0,-6]);m.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
 holecentres=[]
 for z in [1.5,-4.5]:
  sec=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
  for p in sec.discrete:
   ext=np.ptp(p[:,:2],axis=0)
   if np.allclose(ext,[4,4],atol=.015):
    x,y=p[:-1,0],p[:-1,1];fit=np.linalg.lstsq(np.column_stack([2*x,2*y,np.ones(len(x))]),x*x+y*y,rcond=None)[0];holecentres.append(fit[:2])
 expected=[h['xy'] for h in json.loads((root.parent/'panel-hole-review/corrected-validation.json').read_text())['parts']['T']['holes']]+part['speaker_mounts_xy_mm']
 assert len(holecentres)==len(expected)
 error=max(min(math.dist(c,h) for h in holecentres) for c in expected);assert error<.01
 part['STL_checks']={'watertight':True,'single_connected_body':True,'hole_count':len(holecentres),'hole_center_error_mm':error,'print_min_z_mm':0}
 # Source reference envelope and driver circles in front view.
 for cx in part['speaker_centres_x_mm']:
  ax.add_patch(Rectangle((cx-49.75,-59.8),99.5,44.8,fc='#e5e7e8',ec='#4f5a63',lw=1.3,zorder=1))
  for dx in [-20.9,20.9]:ax.add_patch(Circle((cx+dx,-37.4),17.6,fc='#c9cfd2',ec='#6d7d88',zorder=1))
 # Actual 3D mesh projected in XY: only frontmost flat faces to reduce triangulation clutter.
 from matplotlib.collections import PolyCollection
 face_vertices=m.triangles
 ax.add_collection(PolyCollection(face_vertices[:,:,:2],facecolors='#96bbcf',edgecolors='none',alpha=.30,zorder=2))
 for x,y in expected:ax.add_patch(Circle((x,y),2,fc='white',ec='#185570',lw=1,zorder=4))
 ax.axhline(0,color='#526d7b',lw=1,ls='--',zorder=3);ax.text(0,47,'Panel side',ha='center',fontsize=10)
 ax.set_aspect('equal');ax.set_xlim(-115,115);ax.set_ylim(53,-67);ax.axis('off');ax.set_title(variant.replace('-',' ').title(),fontsize=16)
fig.suptitle('Speaker T-piece extensions · confirmed speaker dimensions · first-fit prototypes',fontsize=17,y=.94)
fig.text(.5,.14,'Blue: carrier. Grey: speaker envelope and cones. Dashed line: panel edge.',ha='center',fontsize=11)
fig.text(.5,.10,'Two 90 mm-spaced mounting holes per speaker; original panel mounting interface retained.',ha='center',fontsize=11)
fig.text(.5,.06,'Stepped carriers require supports in the supplied STL orientation. Verify one single and one twin before batch printing.',ha='center',fontsize=10)
fig.subplots_adjust(top=.83,bottom=.21,wspace=.12);fig.savefig(root/'speaker-carriers-preview.png',dpi=150)
(root/'carrier-validation.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v['STL_checks'] for k,v in r['parts'].items()},indent=2))
