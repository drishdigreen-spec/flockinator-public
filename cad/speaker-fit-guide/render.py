from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
root=Path(__file__).resolve().parent
fig=plt.figure(figsize=(12,5),facecolor='white')
for i,(file,label) in enumerate([('Speaker_post_guide_D5p6.stl','Four-post fit guide: 90 × 36 mm centres'),('Speaker_lug_gap_2p6.stl','Lug fit gauge: 2.6 mm opening')],1):
    m=trimesh.load_mesh(root/'stl'/file)
    ax=fig.add_subplot(1,2,i,projection='3d')
    ax.add_collection3d(Poly3DCollection(m.triangles,facecolors='#b5c6ce',shade=True))
    lo,hi=m.bounds
    ax.set(xlim=(lo[0]-2,hi[0]+2),ylim=(lo[1]-2,hi[1]+2),zlim=(0,hi[2]+2))
    ax.set_box_aspect(list(m.extents))
    ax.view_init(25,-55);ax.set_proj_type('ortho');ax.set_axis_off()
    ax.set_title(label,fontsize=11)
fig.suptitle('First speaker fit prints — no retaining barbs or load rating',fontsize=14)
fig.tight_layout()
fig.savefig(root/'fit-guide-preview.png',dpi=150)
