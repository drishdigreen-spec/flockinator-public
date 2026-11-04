import FreeCAD as A, Part, MeshPart, Mesh, json, math, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
R=Path('/Volumes/devops/flockinator/cad/conductor-7inch/terminal-fresh-v6');(R/'stl').mkdir(exist_ok=True)
d=A.ActiveDocument
parts=[('Housing',d.getObject('Cut_TextInlay'),0),('TextInlay',d.getObject('Text_Inlay_Geometry'),1),('BezelInlay',d.getObject('Bezel_Inlay_Geometry'),1),('Base',d.getObject('Fillet_BaseCorners'),1)]
meshes={};records=[]
for name,o,color in parts:
 shape=o.Shape
 assert shape.isValid(),name
 shape.check(True)
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.01,AngularDeflection=math.radians(5),Relative=False)
 points,facets=mesh.Topology
 mesh=Mesh.Mesh([[tuple(round(v,6) for v in points[i]) for i in tri] for tri in facets]);mesh.removeDuplicatedFacets();mesh.fixDegenerations();mesh.harmonizeNormals()
 assert mesh.isSolid(),name
 mesh.write(str(R/'stl'/('FLOCKINATOR_v06_'+name+'.stl')))
 meshes[name]=mesh
 records.append({'part':name,'valid':True,'mesh_solid':True,'solids':len(shape.Solids),'triangles':mesh.CountFacets,'bounds_mm':[shape.BoundBox.XLength,shape.BoundBox.YLength,shape.BoundBox.ZLength]})
# Standard 3MF model packages, colour/material resources. Unsliced.
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def tag(n):return '{'+ns+'}'+n
def plate(filename,names):
 root=ET.Element(tag('model'),{'unit':'millimeter','xml:lang':'en-US'})
 ET.SubElement(root,tag('metadata'),{'name':'Title'}).text='FLOCKINATOR fresh terminal v06 - unsliced study'
 res=ET.SubElement(root,tag('resources'));materials=ET.SubElement(res,tag('basematerials'),{'id':'1'})
 for name,c in [('Warm beige matte','#C8BFA9FF'),('Brown-black accent','#2B2622FF')]:ET.SubElement(materials,tag('base'),{'name':name,'displaycolor':c})
 build=ET.SubElement(root,tag('build'))
 for idx,name in enumerate(names,2):
  color=next(c for n,o,c in parts if n==name)
  obj=ET.SubElement(res,tag('object'),{'id':str(idx),'type':'model','name':name,'pid':'1','pindex':str(color)})
  me=ET.SubElement(obj,tag('mesh'));vs=ET.SubElement(me,tag('vertices'));ts=ET.SubElement(me,tag('triangles'))
  points,facets=meshes[name].Topology
  for v in points:ET.SubElement(vs,tag('vertex'),{'x':str(v.x),'y':str(v.y),'z':str(v.z)})
  for tri in facets:ET.SubElement(ts,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,tri))))
  ET.SubElement(build,tag('item'),{'objectid':str(idx),'transform':'1 0 0 0 1 0 0 0 1 100 125 '+('-3' if name!='Base' else '0')})
 with zipfile.ZipFile(R/filename,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
  z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
  z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
plate('FLOCKINATOR_v06_PlateA.3mf',['Housing','TextInlay','BezelInlay'])
plate('FLOCKINATOR_v06_PlateB.3mf',['Base'])
# No part overlaps with its accent inlays; screen and lens are visual references.
checks=[]
for n1,o1,c in parts:
 for n2,o2,c2 in parts:
  if n1<n2:
   overlap=o1.Shape.common(o2.Shape).Volume
   assert overlap<.001,(n1,n2,overlap)
   checks.append({'parts':[n1,n2],'overlap_mm3':overlap})
(R/'validation.json').write_text(json.dumps({'status':'Fresh style/engineering study, not hardware-fit or slicer verified','parts':records,'overlaps':checks,'master_fully_constrained':d.getObject('SK_Master_Side').FullyConstrained,'screen_rake_from_vertical':20,'deck_from_horizontal':15,'shell_origin':'base footprint centre, Z=0 at base bottom','mesh_tolerance_mm':.01,'mesh_angle_deg':5},indent=2))
# Opposite angle displays horizontal grille.
Gui.activeDocument().activeView().viewAxonometric()
ori=Gui.activeDocument().activeView().getCameraOrientation();Gui.activeDocument().activeView().setCameraOrientation(A.Rotation(A.Vector(0,0,1),-90).multiply(ori).Q)
Gui.activeDocument().activeView().fitAll();Gui.activeDocument().activeView().saveImage(str(R/'grille-side.png'),1600,1100,'White')
# Restore front view on opening.
Gui.activeDocument().activeView().viewAxonometric();ori=Gui.activeDocument().activeView().getCameraOrientation();Gui.activeDocument().activeView().setCameraOrientation(A.Rotation(A.Vector(0,0,1),180).multiply(ori).Q);Gui.activeDocument().activeView().fitAll();d.save()
print(json.dumps({'parts':records,'overlap_checks':len(checks),'exports':'STEP, FCStd, 2 colour/material 3MF packages and 4 STL files'}))
