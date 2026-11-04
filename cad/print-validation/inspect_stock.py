from pathlib import Path
import trimesh,numpy as np,json
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[2]
b=root/'references/duality-track-system-bundle-original-track-and-evolution-pack-model_files'
files=['track_90_150.stl','SeamlessMatteHex/skin_mattehex_90_150_lh.stl','track_straight_100.stl','SeamlessMatteHex/skin_mattehex_straight_100.stl','track_tee_150.stl','SeamlessMatteHex/skin_mattehex_tee_150.stl']
report={}
for f in files:
 m=trimesh.load_mesh(b/f);v=m.vertices
 out={'bounds_source_xyz_mm':m.bounds.tolist(),'extents_mm':m.extents.tolist(),'watertight':bool(m.is_watertight),'faces':len(m.faces)}
 if '90_150' in f:
  # Source90 -> lower-left grid corner: (source z-50,-source x).
  xy=np.column_stack([v[:,2]-50,-v[:,0]])
  polys=[]
  panel=box(20,20,180,180)
  for tri in xy[m.faces]:
   if tri[:,0].max()<20 or tri[:,1].max()<20:continue
   poly=Polygon(tri)
   if poly.area>1e-9 and poly.intersects(panel):polys.append(poly.intersection(panel))
  overlap=unary_union(polys) if polys else Polygon()
  out['panel_overlap_projection_mm2_at_200pitch']=float(overlap.area)
  out['overlap_bounds_mm']=list(overlap.bounds) if not overlap.is_empty else None
 report[f]=out
(root/'cad/print-validation/stock-geometry-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
