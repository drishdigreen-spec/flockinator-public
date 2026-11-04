"""Orthographic CAD triangle renderer with per-pixel depth, avoiding painter-order artifacts."""
from pathlib import Path
import numpy as np,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
colors={'Shell':'#efeee4','Grille':'#292d32','Integrated':'#c7c9c8','Retainer':'#747b7f','Speaker':'#292d32','Fibre':'#b6a686'}
def collect(variant,exploded=False):
 items=[]
 for f in sorted((root/'preview-meshes').glob(variant+'-*.stl')):
  label=f.stem[len(variant)+1:];m=trimesh.load(f)
  if not exploded and any(k in label for k in ['Retainer','Fibre']):continue
  if exploded:
   dz=-24 if 'Grille' in label else 110 if 'Integrated' in label else 90 if 'Fibre' in label else 75 if 'Retainer' in label else 55 if 'Speaker' in label else 0
   m.apply_translation([0,0,dz])
  color=next(v for k,v in colors.items() if k in label);items.append((m,np.array(matplotlib.colors.to_rgb(color))))
 return items

def render(items,elev,azim,width=1100,height=630):
 el,az=np.radians([elev,azim]);eye=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
 right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right);basis=np.stack([right,-up,eye],axis=1)
 tri=np.concatenate([m.triangles for m,col in items]);norm=np.concatenate([m.face_normals for m,col in items]);rgb=np.concatenate([np.tile(col,(len(m.faces),1)) for m,col in items])
 projected=tri@basis;lo=projected[:,:,:2].min((0,1));hi=projected[:,:,:2].max((0,1));scale=min((width-90)/(hi[0]-lo[0]),(height-45)/(hi[1]-lo[1]));centre=(lo+hi)/2
 projected[:,:,:2]=(projected[:,:,:2]-centre)*scale+[width/2,height/2]
 light=eye+up*.6-right*.5;light/=np.linalg.norm(light);shades=.58+.42*np.clip(norm@light,0,1);rgb=(rgb*shades[:,None]*255).astype(np.uint8)
 canvas=np.full((height,width,3),255,dtype=np.uint8);depth=np.full((height,width),-np.inf)
 for t,color in zip(projected,rgb):
  x0,y0=np.maximum(np.floor(t[:,:2].min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(t[:,:2].max(0)).astype(int),[width-1,height-1])
  if x1<x0 or y1<y0:continue
  a,b,c=t;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-9:continue
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
  v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
  z=u*a[2]+v*b[2]+w*c[2];old=depth[y0:y1+1,x0:x1+1];mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(z>old)
  old[mask]=z[mask];canvas[y0:y1+1,x0:x1+1][mask]=color
 return canvas
fig,axes=plt.subplots(2,2,figsize=(15,9),facecolor='white')
for ax,var,ex,el,az,title in zip(axes.ravel(),['single-left','single-left','twin','single-left'],[False,False,False,True],[-30,30,-35,25],[-62,-62,-65,-60],['Single · front honeycomb guard','Rear cover and original T mounting interface','Twin · 118 mm centres / 2 mm gap','Exploded · cover, fibre, retainer, speaker, shell, grille']):
 ax.imshow(render(collect(var,ex),el,az));ax.axis('off');ax.set_title(title,fontsize=13)
fig.suptitle('Flockinator · fully enclosed speaker prototype v2',fontsize=20,y=.98)
fig.text(.5,.035,'116 × 62 × 40 mm per enclosure · 50% gyroid / 5 wall loops requested · CAD verified, physical fit and slicing pending',ha='center',fontsize=11)
fig.text(.5,.01,'Speaker and fibre are dimensional proxies. Exploded gaps are illustrative. Panel surface omitted.',ha='center',fontsize=9)
fig.subplots_adjust(top=.90,bottom=.08,hspace=.10,wspace=.04);fig.savefig(root/'enclosed-speaker-preview.png',dpi=150)
print('Depth-correct CAD preview saved')
