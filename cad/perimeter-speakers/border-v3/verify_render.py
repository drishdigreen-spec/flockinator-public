"""Independent manufacturing-mesh checks and depth-buffer renders of exported CAD."""
from pathlib import Path
import json, math, hashlib, csv, zipfile
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
from render_depth import render
report=json.loads((ROOT/'validation.json').read_text())
for name,p in report['parts'].items():
    path=ROOT/'parts'/(p['stem']+'.stl');m=trimesh.load(path,force='mesh')
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1,name
    assert abs(m.bounds[0,2])<1e-5
    assert np.allclose(m.extents,p['size_mm'],atol=.06),(name,m.extents,p['size_mm'])
    p.update({'mesh_watertight':True,'mesh_single_component':True,'mesh_winding_consistent':True,'stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# Recover the two panel-mount bores from an exported mesh section at actual Z1.5.
# STL cover origin moved +3.5mm from its lowest retaining posts.
cover=trimesh.load(ROOT/'parts/Flockinator-straight-rear-cover-v3.stl',force='mesh')
section=cover.section(plane_origin=[0,0,5.0],plane_normal=[0,0,1])
recovered=[]
for line in section.discrete:
    lo=line[:,:2].min(0); hi=line[:,:2].max(0)
    if np.allclose(hi-lo,[4,4],atol=.05):recovered.append((lo+hi)/2)
for expected in [[-45,7],[45,7]]:
    error=min(np.linalg.norm(x-expected) for x in recovered)
    assert error<.02,(expected,recovered)
report['checks']['exported_mesh_edge_holes']={'expected_xy_mm':[[-45,7],[45,7]],'max_centre_error_mm':max(min(np.linalg.norm(x-e) for x in recovered) for e in [[-45,7],[45,7]])}
# Independent static clip-hole and depth measurements.
report['checks']['printer_envelope']={'verified_model':'Bambu Lab X2D','source':'https://blog.bambulab.com/xcellence-made-simple-bambu-lab-presents-the-x2d/','dual_nozzle_intersection_mm':[235.5,256,256],'all_parts_fit_individually':all(np.all(np.array(p['size_mm'])<[235.5,256,256]) for p in report['parts'].values())}
assert report['checks']['printer_envelope']['all_parts_fit_individually']
(ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

COLORS={'straight-shell':'#e7e7df','straight-grille':'#f5f3e9','straight-rear-cover':'#c6c9c8','speaker-retainer':'#6d7276','corner-shell':'#f5f3e9','corner-rear-cover':'#c6c9c8','snap-bridge':'#3c6476','speaker-REFERENCE':'#25282c','fibre-REFERENCE':'#b0a187'}
meshes={name:trimesh.load(ROOT/'preview-meshes'/(name+'.stl'),force='mesh') for name in COLORS}
def item(name,angle=0,translation=(0,0,0),zextra=0,color=None):
    m=meshes[name].copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle),[0,0,1]));m.apply_translation(np.array(translation)+[0,0,zextra])
    return m,np.array(matplotlib.colors.to_rgb(color or COLORS[name]))
def block(bounds,col):
    lo,hi=np.array(bounds);m=trimesh.creation.box(hi-lo);m.apply_translation((hi+lo)/2);return m,np.array(matplotlib.colors.to_rgb(col))
placements=[(0,0,0),(90,640,0),(180,640,640),(270,0,640)]
full=[]
for angle,x,y in placements:
    rot=trimesh.transformations.rotation_matrix(math.radians(angle),[0,0,1])[:3,:3]
    for k in range(4):
        t=rot@np.array([80+160*k,0,0])+[x,y,0]
        for name in ['straight-shell','straight-grille','straight-rear-cover','speaker-REFERENCE']:full.append(item(name,angle,t))
    for name in ['corner-shell','corner-rear-cover']:full.append(item(name,angle,(x,y,0)))
    for seam in range(5):
        for cy in [-20,-52]:full.append(item('snap-bridge',angle,rot@np.array([160*seam,cy,0])+[x,y,0]))
for row in range(4):
    for col in range(4):full.append(block([[160*col+.6,160*row+.6,-10],[160*(col+1)-.6,160*(row+1)-.6,0]],'#20272d'))
# Camera sees front along -Z, top of panel is smaller Y.
fig,ax=plt.subplots(figsize=(10,10),facecolor='white')
ax.imshow(render(full,-89.9,90,1400,1400));ax.axis('off')
ax.set_title('Flockinator · continuous speaker border',fontsize=20,pad=12)
fig.text(.5,.045,'16 enclosed speakers · four per side at 160 mm centres · rounded corner sections',ha='center',fontsize=11)
fig.text(.5,.022,'780 × 780 mm overall · white honeycomb front · CAD prototype, fit and slicing pending',ha='center',fontsize=10)
fig.subplots_adjust(top=.93,bottom=.07,left=.02,right=.98);fig.savefig(ROOT/'border-front.png',dpi=150);plt.close(fig)
# Local assembly close-up of top-left corner and two adjoining full straights.
close=[]
for name in ['corner-shell','corner-rear-cover']:close.append(item(name))
for angle,t in [(0,(80,0,0)),(270,(0,80,0))]:
    for name in ['straight-shell','straight-grille','straight-rear-cover','speaker-REFERENCE']:close.append(item(name,angle,t))
for cy in [-20,-52]:close.append(item('snap-bridge',translation=(0,cy,0)));close.append(item('snap-bridge',angle=90,translation=(cy,0,0)))
close.append(block([[.1,.1,-10],[159.9,159.9,0]],'#20272d'))
exploded=[]
for name,dz in [('straight-grille',-20),('straight-shell',0),('speaker-REFERENCE',45),('speaker-retainer',60),('fibre-REFERENCE',78),('straight-rear-cover',95)]:exploded.append(item(name,zextra=dz))
fig,axes=plt.subplots(2,2,figsize=(15,11),facecolor='white')
for ax,items,el,az,title in [(axes[0,0],full,-48,65,'Assembled · white continuous border'),(axes[0,1],close,-35,60,'Rounded corner and overlapping fascia'),(axes[1,0],close,40,55,'Rear · shared corner brace and replaceable snap clips'),(axes[1,1],exploded,22,55,'One segment · grille, shell, speaker, retainer, fibre, cover')]:
    ax.imshow(render(items,el,az,1100,750));ax.axis('off');ax.set_title(title,fontsize=12)
fig.suptitle('Flockinator · modular enclosed speaker border v3',fontsize=20,y=.985)
fig.text(.5,.035,'160 mm module pitch · 68 mm border width · 38 mm case depth · longest part 163.8 mm',ha='center',fontsize=11)
fig.text(.5,.014,'Actual CAD geometry. Plain panel envelopes and speaker/fibre proxies; snap fit and acoustic behaviour require physical testing.',ha='center',fontsize=9)
fig.subplots_adjust(top=.94,bottom=.06,hspace=.06,wspace=.04);fig.savefig(ROOT/'border-preview.png',dpi=150);plt.close(fig)
# Small printable snap trial arrangement rendered separately.
snap=[]
for name,col,offset in [('snap-test-posts','#e4e2d9',0),('snap-bridge','#345d70',15),('snap-bridge-loose','#70777f',28)]:
    m=trimesh.load(ROOT/'preview-meshes'/(name+'.stl'),force='mesh');m.apply_translation([0,offset,0]);snap.append((m,np.array(matplotlib.colors.to_rgb(col))))
fig,ax=plt.subplots(figsize=(8,5));ax.imshow(render(snap,40,55,1000,620));ax.axis('off');ax.set_title('Start here · two clip throats and paired test posts');fig.text(.5,.04,'3.2 mm throat (blue) / 3.6 mm throat (grey) · same Ø4 mm necks · static geometry only',ha='center',fontsize=9);fig.savefig(ROOT/'snap-coupon.png',dpi=140);plt.close(fig)
print(json.dumps({'mesh_parts_checked':len(report['parts']),'renders':['border-front.png','border-preview.png','snap-coupon.png']}))
