"""Software orthographic renderer of actual CAD triangles."""
import numpy as np

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
