"""Create a 5 mm variant from the preserved flush model using FreeCAD's runtime."""
import sys
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
import json
from pathlib import Path

root=Path(__file__).resolve().parent
d=A.openDocument(str(root/'Flockinator-flush-reference.FCStd'))
raised=[]
for o in d.Objects:
    if o.Name.startswith(('Panel_REFERENCE','Pixel_diffuser_REFERENCE','Pixel_texture_ILLUSTRATIVE')):
        o.Placement.Base.z+=5
        raised.append(o.Name)
for o in list(d.Nodes.Group):
    if o.Name.startswith('Panel_REFERENCE'):
        b=o.Shape.BoundBox
        ring=Part.makeBox(160,160,5,A.Vector(b.XMin,b.YMin,63)).cut(Part.makeBox(154,154,7,A.Vector(b.XMin+3,b.YMin+3,62)))
        r=d.addObject('Part::Feature','Five_mm_panel_riser_REFERENCE')
        r.Shape=ring
        d.Nodes.addObject(r)
d.recompute()
assert all(o.Shape.isValid() for o in d.Objects if hasattr(o,'Shape'))
panels=[o for o in d.Nodes.Group if o.Name.startswith('Pixel_diffuser_REFERENCE')]
track=d.getObject('Rounded_diffuser_network_REFERENCE')
assert len(panels)==16
assert all(abs(o.Shape.BoundBox.ZMax-track.Shape.BoundBox.ZMax-5)<1e-6 for o in panels)
d.saveAs(str(root/'Flockinator-raised-5mm.FCStd'))
# Export surface triangles for a standalone preview; hide illustrative pixel lines.
surfaces=[]
for category in ['Carrier','Lighting','Nodes','Frame']:
    for o in d.getObject(category).Group:
        if o.Name.startswith('Pixel_texture'): continue
        verts,faces=o.Shape.tessellate(1.5)
        color=(.9,.91,.89)
        if 'Acrylic' in o.Name: color=(.62,.83,.9)
        elif 'diffuser_network' in o.Name: color=(.12,.7,.68)
        elif 'Pixel_diffuser' in o.Name: color=(.27,.46,.55)
        elif 'Panel_REFERENCE' in o.Name or 'Frame_' in o.Name: color=(.1,.13,.15)
        elif 'Aluminium' in o.Name or 'plate' in o.Name: color=(.65,.68,.71)
        surfaces.append({'name':o.Name,'color':color,'vertices':[[v.x,v.y,v.z] for v in verts],'faces':faces})
(root/'raised-surfaces.json').write_text(json.dumps(surfaces))
(root/'raised-5mm-validation.json').write_text(json.dumps({'panel_count':16,'panel_face_z_mm':77,'channel_face_z_mm':72,'projection_mm':5,'valid_shapes':True,'print_ready':False},indent=2))
print('Saved raised model; all sixteen panel faces verified 5 mm proud.')
