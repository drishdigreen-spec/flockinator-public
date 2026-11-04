import pytest
from node_commissioner.sd import prepare, start, validate_result
MAC='00:11:22:33:44:55'
CARD='01'*40
TOKEN='ab'*16

def status(phase='READY', job=8):
    return dict(base_mac=MAC,label='B1',boot_count=1,app_sha256='cd'*32,sd=dict(card_id=CARD,capacity_bytes=32_000_000_000,sector_bytes=512,presence='RESPONDING',maintenance_supported=True,format_token=TOKEN,test=dict(job=job,phase=phase,mode='quick',target_bytes=16*1024*1024,written_bytes=16*1024*1024,read_bytes=16*1024*1024)))

class Fake:
    def __init__(self, changed=None):self.calls=[];self.changed=changed
    def request(self, method, path, body=b''):
        self.calls.append((method,path,body))
        if method=='POST':return dict(ok=True,job=8)
        return self.changed if self.changed is not None and len(self.calls)>1 else status()

def test_prepare_requires_same_identified_node():
    s=status();s['label']='C1'
    with pytest.raises(ValueError):prepare(Fake(s),MAC,'B1',sleep=lambda _:None)

def test_card_change_during_inspection_rejects():
    s=status();s['sd']['card_id']='02'*40
    with pytest.raises(ValueError):prepare(Fake(s),MAC,'B1',sleep=lambda _:None)

def test_erasure_needs_explicit_flag():
    f=Fake()
    with pytest.raises(ValueError):start(f,MAC,'B1','quick',erase=False)
    assert not f.calls


def test_observation_does_not_prepare_or_format():
    from node_commissioner.sd import observe
    f=Fake();observe(f,MAC,'B1')
    assert f.calls==[('GET','/v1/status',b'')]

def test_format_is_bound_to_inspected_card():
    import json
    f=Fake();accepted,inspected=start(f,MAC,'B1','quick',erase=True,sleep=lambda _:None)
    command=json.loads(f.calls[-1][2])
    assert command==dict(op='sd_format_quick',card_id=CARD,token=TOKEN)
    assert accepted['job']==8

def test_false_pass_or_wrong_job_rejected():
    s=status('PASSED')
    validate_result(s,8)
    s['sd']['test']['read_bytes']-=1
    with pytest.raises(ValueError):validate_result(s,8)
    with pytest.raises(ValueError):validate_result(status('PASSED'),9)

def test_radio_report_64bit_capacity_and_bounds():
    from node_commissioner.sd_console import decode_report
    p=bytearray(144);p[1]=1;p[2]=6;p[3]=31
    p[72:80]=(64021856256).to_bytes(8,'little')
    code,sd=decode_report(p.hex())
    assert code==0 and sd['capacity_bytes']==64021856256
    assert sd['test']['mode']=='full'
    p[2]=9
    with pytest.raises(ValueError):decode_report(p.hex())
    with pytest.raises(ValueError):decode_report('00')

def test_format_permits_are_redacted():
    from node_commissioner.evidence import redact
    assert redact(dict(sd=dict(format_token=TOKEN)))['sd']['format_token']=='[REDACTED]'

def test_radio_waits_for_fresh_health_after_usb_reboot(monkeypatch):
    from node_commissioner.sd_console import ConsoleSdClient
    monkeypatch.setattr('node_commissioner.sd_console.time.sleep',lambda _:None)
    class Console:
        polls=0
        def request(self, op, **fields):
            if op=='status':
                self.polls+=1
                return dict(nodes=[dict(label='B1',mac=MAC,registered=True,observed=self.polls>1,age_ms=0,boots=4,version='0.5.1',image_sha256='cd'*32)])
            if op=='sd_request':return dict(node_mac=MAC,transaction='ab'*16)
            p=bytearray(144);p[1]=1;p[3]=16
            return dict(node_mac=MAC,complete=True,report_hex=p.hex())
    console=Console();s=ConsoleSdClient(console,MAC,'B1').request('GET','/v1/status')
    assert console.polls==2 and s['base_mac']==MAC


def test_radio_rejects_wrong_roster_identity(monkeypatch):
    from node_commissioner.sd_console import ConsoleSdClient
    class Console:
        def request(self,op,**fields):return dict(nodes=[dict(label='B1',mac='00:11:22:33:44:55',registered=True,observed=True)])
    with pytest.raises(ValueError):ConsoleSdClient(Console(),MAC,'B1').request('GET','/v1/status')

def test_radio_distinguishes_mounted_non_fat32_from_mount_failure():
    from node_commissioner.sd_console import decode_report
    p=bytearray(144);p[1]=1;p[3]=17 # responding, worker ready, not FAT32
    _,sd=decode_report(p.hex());assert sd['filesystem']=='UNSUPPORTED'
    p[12:16]=(13).to_bytes(4,'little')
    _,sd=decode_report(p.hex());assert sd['filesystem']=='UNMOUNTABLE'
