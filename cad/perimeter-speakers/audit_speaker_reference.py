"""Read the supplied speaker mock-up; uv run --with trimesh --with scipy --with networkx --with matplotlib."""
from pathlib import Path
import json,hashlib,shutil,math
import numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
root=Path(__file__).resolve().parent;out=root/'speaker-reference';out.mkdir(exist_ok=True)
source=Path('$HOME')
m=trimesh.load(source);parts=m.split(only_watertight=False)
flanges=[p for p in parts if np.allclose(p.bounds[:,2],[0,2.15],atol=1e-4)]
assert len(flanges)==1
flange=flanges[0];loops=flange.section(plane_origin=[0,0,1],plane_normal=[0,0,1]).discrete
holes=[]
for loop in loops:
 lo,hi=loop.min(axis=0),loop.max(axis=0)
 if max(hi[:2]-lo[:2])<10:
  holes.append({'xy_mm':((lo[:2]+hi[:2])/2).round(4).tolist(),'diameter_mm':float(np.mean(hi[:2]-lo[:2]))})
assert len(holes)==4
assert {tuple(h['xy_mm']) for h in holes}=={(x,y) for x in [-45,45] for y in [-18,18]}
r={'status':'Third-party mock-up measured; owner confirmed body, mounting centres and depths on 11 October 2026','source_url':'https://www.printables.com/model/1274311-waveshare-8o-5w-speaker/files','source_file':str(source),'author':'Francois Stander','license':'CC BY 4.0','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'body_width_height_mm':[99.5,44.8],'overall_with_lead_stub_mm':m.extents.tolist(),'mounting_pattern_mm':[90,36],'flange_thickness_mm':2.15,'mounting_flange_lower_face_z_mm':0,'rear_projection_from_flange_lower_face_mm':9,'front_projection_from_flange_lower_face_mm':12.2987,'holes':holes,'mesh_parts':len(parts),'note':'Source is a multi-part visual reference, not a manufacturing drawing. Hole openings are in the flange submesh; overlapping other components mean they must not be treated as verified full-depth bores or a screw specification.'}
existing=json.loads((out/'dimensions.json').read_text()) if (out/'dimensions.json').exists() else {}
if 'owner_confirmation' in existing:r['owner_confirmation']=existing['owner_confirmation']
(out/'dimensions.json').write_text(json.dumps(r,indent=2)+'\n');shutil.copyfile(source,out/'speaker-reference-original.stl')
fig,(ax,side)=plt.subplots(2,1,figsize=(11,7),gridspec_kw={'height_ratios':[3,1]},facecolor='white')
ax.add_patch(Rectangle((-49.75,-22.4),99.5,44.8,fc='#e7e9ea',ec='#4c5a66',lw=1.4))
for h in holes:
 x,y=h['xy_mm'];ax.add_patch(Circle((x,y),h['diameter_mm']/2,fc='white',ec='#166f96',lw=1.5));ax.plot(x,y,'+',color='#166f96',ms=4)
for x in [-20.9,20.9]:ax.add_patch(Circle((x,0),17.5,fill=False,ec='#8b949c',lw=1.4))
ax.annotate('',xy=(-45,28),xytext=(45,28),arrowprops={'arrowstyle':'<->'});ax.text(0,30,'90 mm mounting centres',ha='center')
ax.annotate('',xy=(57,-18),xytext=(57,18),arrowprops={'arrowstyle':'<->'});ax.text(59,0,'36 mm',rotation=90,va='center')
ax.set(xlim=(-65,67),ylim=(-30,38));ax.set_aspect('equal');ax.axis('off')
side.add_patch(Rectangle((-49.75,-9),99.5,9,fc='#c4ccd1',ec='#4c5a66'))
side.add_patch(Rectangle((-49.75,0),99.5,2.15,fc='#186e97',ec='#186e97'))
side.add_patch(Rectangle((-49.75,2.15),99.5,10.149,fc='#e7e9ea',ec='#4c5a66'))
side.axhline(0,color='#186e97',ls='--',lw=.6)
side.text(52,-5,'9 mm rear depth',fontsize=10,va='center');side.text(52,6,'12.3 mm to front',fontsize=10,va='center')
side.set(xlim=(-65,95),ylim=(-13,16));side.set_aspect('equal');side.axis('off')
fig.suptitle('Speaker reference: primary dimensions confirmed by owner',fontsize=17,y=.97)
fig.text(.5,.09,'Body: 99.5 × 44.8 mm · depth: 21.3 mm · flange: 2.15 mm · model openings: Ø6.3 mm',ha='center',fontsize=11)
fig.text(.5,.052,'Blue flange datum: lower face at Z=0. Side view is an envelope, not internal construction.',ha='center',fontsize=10)
fig.text(.5,.02,'Source: Francois Stander, Printables #1274311, CC BY 4.0 · model reference; carrier physical fit pending',ha='center',fontsize=9)
fig.subplots_adjust(top=.88,bottom=.14,hspace=.12);fig.savefig(out/'dimensions-to-check.png',dpi=160)
# 1:1 flat flange template including scale reference. No print-ready support geometry.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="130mm" height="95mm" viewBox="0 0 130 95">','<rect width="130" height="95" fill="white"/>','<text x="10" y="8" font-size="3.5">Waveshare speaker model — hardware comparison</text>','<rect x="15.25" y="15.6" width="99.5" height="44.8" fill="none" stroke="black" stroke-width="0.25"/>']
for h in holes:
 x,y=h['xy_mm'];x+=65;y+=38
 svg +=[f'<circle cx="{x}" cy="{y}" r="3.15" fill="none" stroke="#186e97" stroke-width="0.2"/>',f'<path d="M{x-4},{y}h8 M{x},{y-4}v8" stroke="#186e97" stroke-width="0.15"/>']
svg +=['<path d="M15,73h100 M15,71v4 M115,71v4" stroke="black" stroke-width="0.2"/>','<text x="15" y="81" font-size="3">100 mm scale line — print at 100%, no fit to page.</text>','<text x="15" y="88" font-size="2.7">Francois Stander / Printables 1274311 / CC BY 4.0 reference</text>','</svg>'];(out/'speaker-flange-template-1to1.svg').write_text('\n'.join(svg))
print(json.dumps(r,indent=2))
