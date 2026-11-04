"""Create reproducible, metadata-free prototype handoff archives."""
from pathlib import Path
import json,csv,zipfile,hashlib
ROOT=Path(__file__).resolve().parent
settings={'format':'human-readable manufacturing requirements; not a Bambu Studio preset','status':'unsliced prototype','infill_pattern':'gyroid','infill_percent':50,'wall_loops':5,'scale_percent':100,'units':'mm','suggested_initial_material':'Bambu PLA Basic Jade White for visible parts; Basic PLA clip coupon','layer_height_mm':'select in actual printer preset; review small snap geometry','supports':'See per-part orientation notes in README; rear covers and overlap ledges need review','printer_jobs_sent':False}
(ROOT/'print-settings.json').write_text(json.dumps(settings,indent=2)+'\n')
mapping={'top':['A1','A2','A3','A4'],'right':['B3','B4','C4','D4'],'bottom':['C3','D3','D2','D1'],'left':['C2','C1','B1','B2']}
with (ROOT/'speaker-routing.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['side','clockwise_position','centre_from_clockwise_start_corner_mm','node_id','extension'])
    for side,nodes in mapping.items():
        for i,node in enumerate(nodes):w.writerow([side,i+1,80+160*i,node,'required; measure route' if node in ['B2','B3','C2','C3'] else 'measure stock 150 mm lead reach'])
assert len(set(sum(mapping.values(),[])))==16
full_files=[p for p in ROOT.rglob('*') if p.is_file() and not p.name.startswith('._') and '__pycache__' not in p.parts and p.suffix not in ['.zip','.FCBak','.pyc'] and p.name!='manifest.json']
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(full_files)}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');full_files.append(ROOT/'manifest.json')
with zipfile.ZipFile(ROOT/'Flockinator-continuous-border-v3.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(full_files):z.write(p,p.relative_to(ROOT))
# One file per part; quantities are explicit in FIRST-PRINT rather than duplicated meshes.
first_files=[p for p in full_files if p.suffix=='.stl' and p.parent.name=='parts']
first_files += [ROOT/name for name in ['FIRST-PRINT.md','README.md','print-settings.json','validation.json','border-front.png','border-preview.png','snap-coupon.png','LICENSE-GPL-3.0.txt']]
with zipfile.ZipFile(ROOT/'Flockinator-border-first-fit-v3.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(first_files):z.write(p,p.relative_to(ROOT))
for filename in ['Flockinator-continuous-border-v3.zip','Flockinator-border-first-fit-v3.zip']:
    with zipfile.ZipFile(ROOT/filename) as z:
        assert z.testzip() is None
        assert not any('._' in n or 'FCBak' in n for n in z.namelist())
    print(filename,(ROOT/filename).stat().st_size,'bytes')
