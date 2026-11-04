"""Full64x64 optical test parts. uv run --with trimesh --with shapely --with mapbox-earcut --with scipy ..."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,trimesh
from shapely.geometry import Polygon
r=Path(__file__).resolve().parent;out=r/'stl';out.mkdir(exist_ok=True)
pitch=2.5;wall=.4;side=160
holes=[]
for y in range(64):
 for x in range(64):
  a=x*pitch+wall/2;b=(x+1)*pitch-wall/2;c=y*pitch+wall/2;d=(y+1)*pitch-wall/2
  holes.append([(a,c),(a,d),(b,d),(b,c)])
profile=Polygon([(-.2,-.2),(160.2,-.2),(160.2,160.2),(-.2,160.2)],holes)
assert profile.is_valid and len(profile.interiors)==4096
parts=[]
for depth in [3,6]:
 m=trimesh.creation.extrude_polygon(profile,depth,engine='earcut');m.process(validate=True)
 assert m.is_watertight and m.is_winding_consistent and m.body_count==1
 assert np.allclose(m.extents,[160.4,160.4,depth])
 name=f'Flockinator_64x64_P2p5_wall0p4_depth{depth}_mm.stl';m.export(out/name)
 parts.append(dict(file=name,dimensions_mm=m.extents.tolist(),cells=4096,pitch_mm=2.5,internal_wall_mm=.4,edge_wall_mm=.4,panel_overhang_per_side_mm=.2,nominal_cell_opening_mm=2.1,watertight=True,connected_bodies=m.body_count,volume_mm3=float(m.volume),status='Optical test geometry; slicing, actual LED centre registration and hardware clearance not yet validated'))
for thick in [.3,.5]:
 m=trimesh.creation.box([160.4,160.4,thick]);m.apply_translation([80,80,thick/2])
 name=f'Flockinator_full_panel_diffusion_sheet_{str(thick).replace(".","p")}_mm.stl';m.export(out/name)
 parts.append(dict(file=name,dimensions_mm=m.extents.tolist(),watertight=bool(m.is_watertight),status='Full-panel removable optical comparison sheet'))
# Original purchased models are local-only optical/mechanical samples, preserved without reshaping.
base=r.parents[1]/'references/duality-track-system-bundle-original-track-and-evolution-pack-model_files'
stock=['track_straight_100.stl','track_90_150.stl','spliceblock.stl','SeamlessMatteHex/skin_mattehex_straight_100.stl','SeamlessMatteHex/skin_mattehex_90_150_lh.stl','SeamlessMatteHex/skin_mattehex_90_150_rh.stl']
stockdir=r/'purchased-original-samples';stockdir.mkdir(exist_ok=True)
for rel in stock:
 source=base/rel;target=stockdir/source.name;shutil.copy2(source,target)
 parts.append(dict(file='purchased-original-samples/'+target.name,source=str(source.relative_to(r.parents[1])),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),status='Unmodified purchased source orientation; place correct print face on bed in slicer; original licence retained'))
(r/'part-manifest.json').write_text(json.dumps(parts,indent=2));print(json.dumps(parts[:4],indent=2))
