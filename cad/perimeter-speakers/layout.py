"""Concept routing only; speaker symbols and extensions are not fabrication geometry."""
from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
out=Path(__file__).resolve().parent
# Clockwise side order; a middle twin carrier plus two single carriers per edge.
side_nodes={'top':['A1','A2','B2','A3'],'right':['A4','B4','B3','C4'],'bottom':['D4','D3','C3','D2'],'left':['D1','C1','C2','B1']}
assert len(set(sum(side_nodes.values(),[])))==16
slots=[140,265,375,500]  # carrier-v1 centres along each edge; symbols remain schematic
fig,ax=plt.subplots(figsize=(10,10),facecolor='white')
for ri,row in enumerate('ABCD'):
 for col in range(4):
  name=f'{row}{col+1}';inner=name in ['B2','B3','C2','C3']
  ax.add_patch(Rectangle((col*160,ri*160),160,160,facecolor='#e3edf3' if inner else '#f1f2f0',edgecolor='#617180',lw=1.2))
  ax.text(col*160+80,ri*160+80,name,ha='center',va='center',fontsize=17,color='#154d6c' if inner else '#3e4f5c')
rows=[]
def xy(side,t,n):
 return {'top':(t,-n),'right':(640+n,t),'bottom':(640-t,640+n),'left':(-n,640-t)}[side]
for side,nodes in side_nodes.items():
 for j,node in enumerate(nodes):
  x,y=xy(side,slots[j],37.4);tx,ty=xy(side,160 if j==0 else 480 if j==3 else 320,0)
  ax.plot([tx,x],[ty,y],color='#718899',lw=3,zorder=1)
  inner=node in ['B2','B3','C2','C3'];color='#146b94' if inner else '#455c68'
  w,h=(99.5,44.8) if side in ['top','bottom'] else (44.8,99.5)
  ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor='white',edgecolor=color,lw=2,zorder=3))
  ax.text(x,y,node,ha='center',va='center',fontsize=10,color=color,zorder=4)
  if inner:
   nx=(int(node[1])-1)*160+80;ny='ABCD'.index(node[0])*160+80
   ax.plot([nx,x],[ny,y],ls='--',lw=1.3,color='#146b94',alpha=.65,zorder=2)
  rows.append({'side':side,'position_clockwise':j+1,'node':node,'carrier':'single 1' if j==0 else 'single 2' if j==3 else 'twin','extended_center_node_lead':inner,'stock_lead_mm':150,'extension_plan':'planned; length to measure' if inner else 'stock lead preferred; routed reach to verify'})
ax.set_aspect('equal');ax.set_xlim(-115,755);ax.set_ylim(755,-115);ax.axis('off')
fig.suptitle('Temporary whiteboard array: perimeter speaker proposal',fontsize=16,y=.96)
fig.text(.5,.075,'16 independent speakers · 4 per side · 8 single carriers + 4 twin carriers',ha='center',fontsize=12)
fig.text(.5,.045,'Dashed lines: centre-node lead extensions. Speaker body outlines are to scale; cable routes are schematic.',ha='center',fontsize=10)
fig.savefig(out/'speaker-layout-concept.png',dpi=150)
with (out/'speaker-routing-proposal.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(out/'concept-status.json').write_text(json.dumps({'status':'Carrier v1 prototypes exported; owner confirmed primary speaker dimensions; physical carrier fit pending','panel_array_nominal_mm':[640,640],'reported_magnetic_standoff_mm':12,'speakers':16,'single_carriers':8,'twin_carriers':4,'speaker_dimensions_owner_confirmed':True,'exported_hole_positions_verified':True,'carrier_physical_fit_verified':False,'printable_speaker_parts_created':True},indent=2)+'\n')
