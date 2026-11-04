from pathlib import Path
import numpy as np
import trimesh
import json
root=Path(__file__).resolve().parent
results=[]
for p in sorted((root/'stl').glob('*.stl')):
    if p.name.startswith('._'):continue
    m=trimesh.load_mesh(p)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,p.name
    assert len(m.split())==1 and abs(m.bounds[0,2])<1e-5,p.name
    if 'post_guide' in p.name:
        loops=m.section(plane_origin=[0,0,17],plane_normal=[0,0,1]).discrete
        centres=sorted(tuple(np.round((a.min(axis=0)+a.max(axis=0))[:2]/2,3)) for a in loops)
        assert centres==[(-46.,-18.),(-46.,18.),(46.,-18.),(46.,18.)],centres
        assert all(abs(np.mean(np.ptp(a[:,:2],axis=0))-5.6)<.03 for a in loops)
        details={'post_pattern_mm':[92,36],'diameter_mm':5.6}
    else:
        gap=float(p.stem.split('gap_')[1].split('_')[0].replace('p','.'))
        ys=np.unique(np.round(m.vertices[np.isclose(m.vertices[:,0],18),1],4))
        assert np.allclose(ys,[0,3,3+gap,6+gap],atol=1e-4),(p.name,ys)
        details={'jaw_gap_mm':gap,'print_orientation_verified':True}
    results.append({'file':p.name,'watertight':True,'connected':True,**details})
assert len(results)==4
(root/'validation.json').write_text(json.dumps(results,indent=2))
print('Four STL meshes pass; 92 x 36 centres, 5.6 mm posts and all jaw gaps verified independently.')
