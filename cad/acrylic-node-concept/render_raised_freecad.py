import sys
sys.path.append('/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import FreeCADGui as G
import Part
from pathlib import Path
root=Path(__file__).resolve().parent
G.showMainWindow()
d=A.openDocument(str(root/'Flockinator-raised-5mm.FCStd'))
for name in ['Carrier','Lighting','Nodes','Frame']:
    for o in d.getObject(name).Group:
        o.ViewObject.Visibility=True
        o.ViewObject.ShapeColor=(.91,.92,.89)
        if 'Acrylic' in o.Name:
            o.ViewObject.ShapeColor=(.64,.85,.93);o.ViewObject.Transparency=65
        elif 'diffuser_network' in o.Name:o.ViewObject.ShapeColor=(.12,.7,.68)
        elif 'Pixel_diffuser' in o.Name:o.ViewObject.ShapeColor=(.27,.46,.55)
        elif 'Panel_REFERENCE' in o.Name or 'Frame_' in o.Name:o.ViewObject.ShapeColor=(.1,.13,.15)
        elif 'Pixel_texture' in o.Name:o.ViewObject.ShapeColor=(.13,.22,.26)
for o in d.ExplodedNode.Group:o.ViewObject.Visibility=False
v=G.activeDocument().activeView()
v.viewAxonometric();v.fitAll();G.updateGui()
v.saveImage(str(root/'raised-5mm.png'),1800,1400,'White')
d.save()
detail=A.newDocument('RaisedDetail')
crop=Part.makeBox(440,440,140,A.Vector(-420,-420,-40))
for category in ['Carrier','Lighting','Nodes','Frame']:
    for o in d.getObject(category).Group:
        shape=o.Shape.common(crop)
        if shape.isNull() or shape.Volume<=0:continue
        dst=detail.addObject('Part::Feature',o.Name)
        dst.Shape=shape
        dst.ViewObject.ShapeColor=o.ViewObject.ShapeColor
        dst.ViewObject.Transparency=o.ViewObject.Transparency
detail.recompute()
v=G.activeDocument().activeView()
v.setCameraOrientation(A.Rotation(A.Vector(0,0,1),-20).multiply(A.Rotation(A.Vector(1,0,0),65)).Q)
v.fitAll();G.updateGui()
v.saveImage(str(root/'raised-5mm-detail.png'),1600,1200,'White')
print('Rendered raised 5 mm model.')
