from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json
import trimesh,numpy as np
base=Path('/Volumes/devops/flockinator/cad/perimeter-speakers/box-reference-lual')
f=base/'8ohm_5w_speaker_boxlual.3mf';ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
with zipfile.ZipFile(f) as z:
 print('Files:',z.namelist())
 tree=ET.fromstring(z.read('3D/3dmodel.model'))
 for obj in tree.findall('m:resources/m:object',ns):
  mesh=obj.find('m:mesh',ns)
  if mesh is None:continue
  vs=[[float(v.get(a)) for a in ['x','y','z']] for v in mesh.find('m:vertices',ns)]
  fs=[[int(t.get(a)) for a in ['v1','v2','v3']] for t in mesh.find('m:triangles',ns)]
  m=trimesh.Trimesh(vs,fs);m.merge_vertices(merge_tex=True,merge_norm=True)
  print('Object',obj.attrib,'bounds',m.bounds.tolist(),'watertight',m.is_watertight,'winding',m.is_winding_consistent,'parts',len(m.split(only_watertight=False)))
  for height in [1.5,5,10,12,16,22]:
   sec=m.section(plane_origin=[0,0,height],plane_normal=[0,0,1])
   if sec:print('Section',height,[np.round([c.min(axis=0),c.max(axis=0)],3).tolist() for c in sec.discrete][:12])
  m.export('/tmp/lual-speaker-box-inspection.stl')
 for n in z.namelist():
  if n.endswith('.config'):
   s=z.read(n).decode();print(n,s[:1600] if 'model' in n else '\n'.join(line for line in s.splitlines() if any(k in line for k in ['layer_height =','nozzle_diameter =','filament_type =','top_solid_layers =','bottom_solid_layers =','fill_density ='])))
