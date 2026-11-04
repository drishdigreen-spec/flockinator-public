from pathlib import Path
import sys,json,itertools
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
root=Path(__file__).resolve().parent
r=json.loads((root/'validation.json').read_text())
def shape(name):
 s=Part.Shape();s.read(str(root/'parts'/('Flockinator-'+name+'-v2.step')));return s
parts=[shape(n) for n in ['speaker-shell','speaker-honeycomb-grille','speaker-retaining-frame']]
checks={}
for variant,centres in [('single-left',[-20]),('single-right',[20]),('twin',[-59,59])]:
 assembly=[shape('speaker-T-cover-'+variant)]
 for x in centres:
  for p in parts:
   q=p.copy();q.translate(A.Vector(x,0,0));assembly.append(q)
 overlaps=[a.common(b).Volume for a,b in itertools.combinations(assembly,2)]
 assert max(overlaps)<1e-6,(variant,max(overlaps))
 checks[variant]={'exported_STEP_part_pairs_checked':len(overlaps),'max_solid_overlap_mm3':max(overlaps)}
r['checks']['exported_STEP_assembly_interference']=checks
(root/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(checks,indent=2))
