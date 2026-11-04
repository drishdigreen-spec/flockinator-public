import hashlib
import pytest
from node_commissioner.image import verify_image

def test_modified_and_truncated_image_rejected(tmp_path):
    p=tmp_path/'firmware.bin'; body=b'\xe9'+b'\0'*100
    data=body+hashlib.sha256(body).digest(); p.write_bytes(data)
    digest=hashlib.sha256(data).hexdigest()
    assert verify_image(p,digest)==hashlib.sha256(body).hexdigest()
    p.write_bytes(data[:-1])
    with pytest.raises(ValueError): verify_image(p,digest)
    p.write_bytes(b'\x00'+data[1:])
    with pytest.raises(ValueError): verify_image(p,hashlib.sha256(p.read_bytes()).hexdigest())
