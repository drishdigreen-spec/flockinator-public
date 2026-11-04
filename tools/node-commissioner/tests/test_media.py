import struct
import pytest
from node_commissioner.media import encode_pack, decode_pack, rgb565

def test_pack_roundtrip():
    frames=[bytes(8192),bytes([255])*8192]
    packed=encode_pack(frames)
    assert decode_pack(packed)==frames
    assert packed[:8]==b'FLKFACE1'

def test_rgb565_primary_colours():
    assert rgb565([(255,0,0),(0,255,0),(0,0,255)])==b'\x00\xf8\xe0\x07\x1f\x00'

@pytest.mark.parametrize('data',[b'',b'FLKFACE1'+struct.pack('<II',999,8192),b'FLKFACE1'+struct.pack('<II',1,8191)+bytes(8191)])
def test_invalid_pack(data):
    with pytest.raises(ValueError):decode_pack(data)

def test_no_trailing_or_truncated_data():
    p=encode_pack([bytes(8192)])
    for altered in (p[:-1],p+b'x'):
        with pytest.raises(ValueError):decode_pack(altered)

def test_bad_frame_size():
    with pytest.raises(ValueError):encode_pack([bytes(8)])
