"""Bounded native 64x64 RGB565 pack, with deterministic local asset conversion."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

FRAME_BYTES = 8192
MAX_FRAMES = 64

def rgb565(pixels):
    return b''.join(struct.pack('<H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)) for r,g,b in pixels)

def encode_pack(frames):
    if not 1 <= len(frames) <= MAX_FRAMES or any(len(f) != FRAME_BYTES for f in frames):
        raise ValueError('Invalid frame count or size')
    return struct.pack('<8sII', b'FLKFACE1', len(frames), FRAME_BYTES) + b''.join(frames)

def decode_pack(data):
    if len(data) < 16:
        raise ValueError('Truncated header')
    magic,count,size=struct.unpack('<8sII',data[:16])
    if magic != b'FLKFACE1' or not 1 <= count <= MAX_FRAMES or size != FRAME_BYTES or len(data) != 16 + count * size:
        raise ValueError('Invalid pack')
    return [data[16+i*size:16+(i+1)*size] for i in range(count)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sleep',type=Path)
    args=p.parse_args()
    from PIL import Image
    names=[f'picture{group}-{frame}.png' for group in range(1,6) for frame in range(1,9)]+['wake1.png','wake2.png']
    frames=[]; manifest=[]
    for name in names:
        path=args.source/name
        with Image.open(path) as image:
            if image.size != (64,64):raise ValueError('Expected native 64x64 image')
            frames.append(rgb565(image.convert('RGB').getdata()))
        manifest.append(dict(index=len(frames)-1,source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    # Slot 42 is an explicit neutral fallback until generated sleep art is accepted.
    if args.sleep:
        with Image.open(args.sleep) as image:
            if image.size != (64,64): raise ValueError('Sleep frame must be 64x64')
            frames.append(rgb565(image.convert('RGB').getdata()))
        manifest.append(dict(index=42,source=str(args.sleep),sha256=hashlib.sha256(args.sleep.read_bytes()).hexdigest(),generated=True))
    else:
        frames.append(frames[32]);manifest.append(dict(index=42,source='healthy-neutral-fallback',fallback=True))
    data=encode_pack(frames);args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'faces.pack').write_bytes(data)
    (args.output/'manifest.json').write_text(json.dumps(dict(schema=1,frames=manifest,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
