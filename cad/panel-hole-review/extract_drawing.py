"""Audit mounting centres from the supplied Waveshare DWG; uv run --with ezdxf.
Converts into this folder using LibreDWG; never modifies the source DWG.
"""
from pathlib import Path
import subprocess,json,hashlib
import ezdxf
root=Path(__file__).resolve().parent
repo=root.parents[1]
source=repo/'references/repos/RGB-Matrix-Px-xx/hardware/dimensions/RGB-Matrix-Pxx-64x64/RGB-Matrix-P2_5-64x64-2D.dwg'
target=root/'Waveshare-P2p5-panel-source.dxf'
with (root/'dwg-conversion.log').open('w') as log:
 subprocess.run(['dwg2dxf','-y','-o',str(target),str(source)],stdout=log,stderr=log,check=True)
doc=ezdxf.readfile(target);m=doc.modelspace()
dim90,dim146=doc.entitydb['39E'],doc.entitydb['3A0']
assert dim90.dxf.text=='90' and dim146.dxf.text=='146'
cx=(dim90.dxf.defpoint2.x+dim90.dxf.defpoint3.x)/2
cy=(dim146.dxf.defpoint2.y+dim146.dxf.defpoint3.y)/2
holes=[];corners=[]
for e in m.query('CIRCLE'):
 c=e.dxf.center;x,y=round(c.x-cx,6),round(c.y-cy,6)
 record={'entity_handle':e.dxf.handle,'center_relative_panel_mm':[x,y],'drawn_radius_mm':e.dxf.radius}
 if abs(e.dxf.radius-1.25)<1e-6 and abs(x)<80 and abs(y)<80:holes.append(record)
 if abs(e.dxf.radius-1.55)<1e-6 and abs(abs(x)-72.5)<1e-6 and abs(abs(y)-72.5)<1e-6:corners.append(record)
assert len(holes)==8 and len(corners)==4
assert {tuple(h['center_relative_panel_mm']) for h in holes}=={(sx*a,sy*b) for sx in [-1,1] for sy in [-1,1] for a,b in [(73,45),(45,73)]}
r={'source':str(source.relative_to(repo)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'drawing_center_xy':[cx,cy],'drawing_shell_size_mm':159.8,'shell_tolerance_mm':.1,'nominal_panel_pitch_mm':160,'M3_edge_holes':holes,'corner_3p1mm_features':corners,'M3_coordinates_top_left_nominal_mm':[[round(h['center_relative_panel_mm'][0]+80,3),round(80-h['center_relative_panel_mm'][1],3)] for h in holes],'basis':'M3-labelled edge holes selected by matching circle geometry and annotations. Corner features are separately dimensioned 145 mm apart; do not equate their diameter callout to a verified thread specification.','near_far_offsets_nominal_mm':[7,35],'near_far_offsets_shell_mm':[6.9,34.9]}
previous=json.loads((root/'panel-hole-coordinates.json').read_text())
assert r==previous,'Source geometry changed: review before regenerating brackets'
print('Source drawing re-extracted: all 8 edge M3 and 4 corner centres match audited coordinates.')
