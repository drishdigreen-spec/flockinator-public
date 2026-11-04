"""Independent STL integrity and post-centre checks; uv run with trimesh/scipy."""
from pathlib import Path
import json
import numpy as np
import trimesh
root=Path(__file__).resolve().parent
results=[]
for path in sorted((root/'stl').glob('*.stl')):
    if path.name.startswith('._'):continue
    m=trimesh.load_mesh(path,process=True)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,path.name
    assert len(m.split())==1,path.name
    assert abs(m.bounds[0,2])<1e-5,path.name
    entry={'file':path.name,'watertight':True,'one_connected_body':True}
    if 'post_guide' in path.name:
        section=m.section(plane_origin=[0,0,17],plane_normal=[0,0,1])
        loops=section.discrete
        centres=sorted(tuple(np.round((p.min(axis=0)+p.max(axis=0))[:2]/2,3)) for p in loops)
        assert centres==[(-45.,-18.),(-45.,18.),(45.,-18.),(45.,18.)],centres
        diameters=[float(np.mean(np.ptp(p[:,:2],axis=0))) for p in loops]
        expected=float(path.stem.rsplit('_D',1)[1].replace('p','.'))
        assert all(abs(v-expected)<.03 for v in diameters),(path,diameters)
        entry.update(post_centres_mm=centres,post_diameter_mm=expected)
    results.append(entry)
assert len(results)==6
(root/'validation.json').write_text(json.dumps(results,indent=2))
print('Six STL meshes pass integrity checks; all three post patterns and diameters verified from mesh sections.')
