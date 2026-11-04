"""Verify STL through-holes independently, then render drawing-alignment overlays.
uv run --with trimesh --with scipy --with networkx --with matplotlib verify_and_render.py
"""
from pathlib import Path
import json,math,numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
root=Path(__file__).resolve().parent
r=json.loads((root/'corrected-validation.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(13,6),facecolor='white')
for ax,(kind,part) in zip(axes,r['parts'].items()):
 mesh=trimesh.load(root/part['files']['stl']);assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
 section=mesh.section(plane_origin=[0,0,1.5],plane_normal=[0,0,1]);loops=section.discrete
 outline=max(loops,key=lambda p:np.prod(np.ptp(p[:,:2],axis=0)))
 holes=[];maxerr=0
 for loop in loops:
  if loop is outline:continue
  x,y=loop[:-1,0],loop[:-1,1]
  # Circle equation x²+y² = 2*cx*x + 2*cy*y + c.
  fitted=np.linalg.lstsq(np.column_stack((2*x,2*y,np.ones(len(x)))),x*x+y*y,rcond=None)[0]
  cx,cy,c=fitted;radius=math.sqrt(c+cx*cx+cy*cy)
  assert abs(radius-2)<.01
  holes.append([cx,cy])
 expected=[h['xy'] for h in part['holes']]
 assert len(holes)==len(expected)
 for expected_center in expected:
  error=min(math.dist(expected_center,actual) for actual in holes);maxerr=max(maxerr,error);assert error<.01
 part['STL_validation']={'watertight':True,'connected_bodies':1,'through_holes':len(holes),'max_hole_center_error_vs_drawing_mm':maxerr,'section_height_mm':1.5}
 ax.fill(outline[:,0],outline[:,1],color='#dae1e7',ec='#384b5c',lw=1.5,zorder=1)
 ax.axvline(0,color='#919aa2',ls='--',lw=1,zorder=0);ax.axhline(0,color='#919aa2',ls='--',lw=1,zorder=0)
 for h in part['holes']:
  x,y=h['xy'];color='#126d9e' if h['kind']=='edge_M3' else '#b55c1c'
  ax.add_patch(Circle((x,y),2,fc='white',ec=color,lw=1.3,zorder=2))
  ax.plot(x,y,'+',color=color,ms=4,zorder=3)
 ax.set_aspect('equal');ax.set_xlim(-47,47);ax.set_ylim((-8,48) if kind=='T' else (-47,47))
 ax.set_title(f'{kind} joint v2 · {len(holes)} holes',fontsize=16,pad=14)
 ax.set_xlabel('mm from panel junction');ax.set_ylabel('mm from outer edge' if kind=='T' else 'mm from panel junction');ax.grid(alpha=.15)
fig.suptitle('Corrected supports: both mounting patterns from the P2.5 drawing',fontsize=18,y=.98)
fig.text(.5,.045,'Blue = edge M3 centres (7 / 35 mm offsets)     Orange = corner mount centres (7.5 / 7.5 mm)',ha='center',fontsize=11)
fig.text(.5,.012,'Nominal 160 mm panel pitch · 4 mm bracket clearance holes · 3 mm plate + 3 mm rear ribs · physical fit pending',ha='center',fontsize=10)
fig.subplots_adjust(top=.84,bottom=.17,wspace=.24);fig.savefig(root/'corrected-joints-overlay.png',dpi=170)
(root/'corrected-validation.json').write_text(json.dumps(r,indent=2)+'\n')
# True-size vector paper template, explicit mm units, nominal panel face outlined.
s=json.loads((root/'panel-hole-coordinates.json').read_text())
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="190mm" height="210mm" viewBox="0 0 190 210">','<rect width="190" height="210" fill="white"/>','<text x="15" y="10" font-size="4">P2.5 panel hole check — nominal 160 mm</text>','<rect x="15" y="20" width="160" height="160" fill="none" stroke="black" stroke-width="0.3"/>']
for key,color in [('M3_edge_holes','#126d9e'),('corner_3p1mm_features','#b55c1c')]:
 for h in s[key]:
  x,y=h['center_relative_panel_mm'];x+=95;y=100-y
  svg +=[f'<circle cx="{x}" cy="{y}" r="2" fill="none" stroke="{color}" stroke-width="0.25"/>',f'<path d="M{x-3},{y}h6 M{x},{y-3}v6" stroke="{color}" stroke-width="0.2"/>']
svg +=['<path d="M15,190h100 M15,188v4 M115,188v4" stroke="black" stroke-width="0.3"/>','<text x="15" y="197" font-size="3.5">This line must measure 100 mm. Print at 100%, no fit-to-page.</text>','<text x="15" y="204" font-size="3.5">Blue: edge M3. Orange: corner mounts. Verify on actual panel.</text>','</svg>']
(root/'panel-hole-template-1to1.svg').write_text('\n'.join(svg))
print(json.dumps({k:v['STL_validation'] for k,v in r['parts'].items()},indent=2))
