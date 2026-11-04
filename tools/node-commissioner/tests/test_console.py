import json
import pytest
from node_commissioner.console import ConsoleClient, check_name

MAC='00:11:22:33:44:55'
class Port:
    def __init__(self, mutate=None): self.mutate=mutate;self.pending=[];self.sent=[];self.read_sizes=[]
    def write(self,data):
        q=json.loads(data);self.sent.append(q)
        reply=dict(v=1,request_id=q['id'],base_mac=MAC,ok=True,type='console_status')
        if self.mutate:self.mutate(reply)
        self.pending=[b'refresh_ms=100\n',json.dumps(reply).encode()+b'\n']
    @property
    def in_waiting(self): return sum(len(chunk) for chunk in self.pending)
    def read(self, size):
        self.read_sizes.append(size)
        data = b''.join(self.pending)
        self.pending = [data[size:]] if data[size:] else []
        return data[:size]
    def close(self):pass

def test_bound_request_skips_logs():
    p=Port();c=ConsoleClient('unused',MAC,serial_port=p)
    assert c.request('status')['base_mac']==MAC
    assert p.sent[0]['target']==MAC

def test_wrong_console_rejected():
    c=ConsoleClient('unused',MAC,serial_port=Port(lambda r:r.update(base_mac='00:11:22:33:44:55')))
    with pytest.raises(ValueError,match='identity'):c.request('status')

def test_device_rejection_preserves_error():
    c=ConsoleClient('unused',MAC,serial_port=Port(lambda r:r.update(ok=False,error='wrong_offset')))
    with pytest.raises(ValueError,match='wrong_offset'):c.request('image_chunk',offset=0,data='01')

def test_image_names_confined():
    assert check_name('node-0.4.0.bin')=='node-0.4.0.bin'
    for name in ['../private','/file','x/y','..','a'*80,'name with spaces.bin']:
        with pytest.raises(ValueError):check_name(name)

def test_no_reserved_fields_or_huge_frame():
    c=ConsoleClient('unused',MAC,serial_port=Port())
    with pytest.raises(ValueError):c.request('status',target='bad')
    with pytest.raises(ValueError):c.request('image_chunk',data='a'*9000)

from copy import deepcopy
from types import SimpleNamespace

NODE_MAC = '00:11:22:33:44:55'
IMAGE = 'a' * 64
BOOT = '1' * 32


def snapshot(*, busy=False, boots=8, verified=False, image='b' * 64):
    return dict(v=1, base_mac=MAC, ok=True, boot_id=BOOT, busy=busy,
                deployment='Deploying to A1' if busy else 'Idle', offset=0 if busy else 1024, total=1024,
                nodes=[dict(label='A1', mac=NODE_MAC, registered=True, observed=True,
                            health='Healthy', age_ms=0, boots=boots, receiver_version=1,
                            image_sha256=image, ota_state=2, deployment_verified=verified)])


class DeploymentClient(ConsoleClient):
    def __init__(self, states, before=None):
        self.mac = MAC
        self.before = before or snapshot()
        self.states = deepcopy(states)
        self.calls = []

    def identify(self):
        return deepcopy(self.before)

    def request(self, op, **fields):
        self.calls.append((op, fields))
        if op == 'deploy':
            return dict(v=1, base_mac=MAC, ok=True, request_id='accepted-request')
        if len(self.states) > 1:
            return self.states.pop(0)
        return self.states[0]


@pytest.fixture
def clock(monkeypatch):
    value = [0.0]
    def sleep(seconds):
        value[0] += seconds
    clock = SimpleNamespace(monotonic=lambda: value[0], sleep=sleep)
    monkeypatch.setattr('node_commissioner.console.time', clock)
    return clock


def verified_snapshot():
    done = snapshot(boots=9, verified=True, image=IMAGE)
    done['deployment'] = 'Verified: expected image booted valid'
    return done


def test_deploy_waits_for_fresh_changed_boot_not_acceptance(clock):
    stages = [snapshot(busy=True), verified_snapshot()]
    client = DeploymentClient(stages)
    progress = []
    result = client.deploy('A1', 'node.bin', IMAGE, timeout=10, progress=progress.append)
    assert result['verified'] is True
    assert result['before_boots'] == 8 and result['after_boots'] == 9
    assert result['console_boot_id'] == BOOT
    assert result['deployment_request_id'] == 'accepted-request'
    assert [call[0] for call in client.calls] == ['deploy', 'status', 'status']
    assert len(progress) == 2
    assert all(set(item) == {'label', 'mac', 'stage', 'offset', 'total'} for item in progress)


@pytest.mark.parametrize('patch', [
    {'boots': 8}, {'image_sha256': 'c'*64}, {'ota_state': 1}, {'receiver_version': 0},
    {'observed': False}, {'age_ms': 30000}, {'health': 'Stale'}, {'deployment_verified': False},
])
def test_unverified_terminal_status_never_returns_success(clock, patch):
    done = verified_snapshot()
    done['nodes'][0].update(patch)
    client = DeploymentClient([done])
    with pytest.raises(RuntimeError, match='without a verified'):
        client.deploy('A1', 'node.bin', IMAGE, timeout=2)


def test_console_reset_invalidates_even_otherwise_verified_result(clock):
    done = verified_snapshot()
    done['boot_id'] = '2'*32
    with pytest.raises(RuntimeError, match='Console rebooted'):
        DeploymentClient([done]).deploy('A1', 'node.bin', IMAGE)


def test_changed_target_identity_invalidates_result(clock):
    done = verified_snapshot()
    done['nodes'][0]['mac'] = '00:11:22:33:44:55'
    with pytest.raises(RuntimeError, match='identity changed'):
        DeploymentClient([done]).deploy('A1', 'node.bin', IMAGE)


def test_remote_failure_is_reported_without_retrying_deploy(clock):
    failed = snapshot()
    failed['deployment'] = 'Failed: radio response timeout'
    client = DeploymentClient([failed])
    with pytest.raises(RuntimeError, match='radio response timeout'):
        client.deploy('A1', 'node.bin', IMAGE)
    assert sum(op == 'deploy' for op, _ in client.calls) == 1


def test_busy_controller_and_missing_session_fail_before_mutation(clock):
    for patch in [{'busy': True}, {'boot_id': ''}]:
        before = snapshot()
        before.update(patch)
        client = DeploymentClient([], before)
        with pytest.raises(ValueError):
            client.deploy('A1', 'node.bin', IMAGE)
        assert client.calls == []


def test_wait_is_bounded_and_does_not_claim_rollback_or_success(clock):
    client = DeploymentClient([snapshot(busy=True)])
    with pytest.raises(TimeoutError, match='accepted but not verified'):
        client.deploy('A1', 'node.bin', IMAGE, timeout=3)
    assert clock.monotonic() == 3
    assert sum(op == 'deploy' for op, _ in client.calls) == 1


def test_invalid_deploy_timeout_and_target_rejected_without_mutation(clock):
    client = DeploymentClient([])
    for timeout in [0, -1, float('inf'), float('nan'), 3601]:
        with pytest.raises(ValueError):
            client.deploy('A1', 'node.bin', IMAGE, timeout=timeout)
    with pytest.raises(ValueError):
        client.deploy('A9', 'node.bin', IMAGE)
    assert client.calls == []


def test_upload_checks_device_offsets_and_final_digest(tmp_path, monkeypatch):
    from node_commissioner import console
    image = tmp_path / 'node.bin'
    image.write_bytes(b'x'*1100)
    monkeypatch.setattr(console, 'verify_image', lambda *_: IMAGE)
    class UploadClient:
        identify = lambda self: {}
        upload = ConsoleClient.upload
        def __init__(self, bad_offset=False, bad_digest=False):
            self.bad_offset = bad_offset
            self.bad_digest = bad_digest
        def request(self, op, **fields):
            if op == 'image_chunk':
                return {'offset': -1 if self.bad_offset else fields['offset']+len(fields['data'])//2}
            if op == 'image_end':
                return {'image_sha256': 'bad' if self.bad_digest else IMAGE}
            return {}
    progress = []
    result = UploadClient().upload(image, 'f'*64, progress=progress.append)
    assert result['bytes'] == 1100
    assert [entry['offset'] for entry in progress] == [0, 512, 1024, 1100]
    with pytest.raises(ValueError, match='offset'):
        UploadClient(bad_offset=True).upload(image, 'f'*64)
    with pytest.raises(ValueError, match='digest'):
        UploadClient(bad_digest=True).upload(image, 'f'*64)


def test_split_usb_packets_and_multiple_log_lines_are_parsed():
    class SplitPort(Port):
        def read(self, size):
            return super().read(min(size, 7))
        def write(self, data):
            super().write(data)
            self.pending.insert(0, b'boot:ready\nnoise\n{"request_id":"old","ok":true}\n')
    port = SplitPort()
    client = ConsoleClient('unused', MAC, serial_port=port)
    assert client.request('status')['base_mac'] == MAC
    assert len(port.read_sizes) > 1


def test_bulk_reader_avoids_one_read_per_reply_byte():
    port = Port(lambda reply: reply.update(padding='x'*7000))
    client = ConsoleClient('unused', MAC, serial_port=port)
    assert len(client.request('status')['padding']) == 7000
    assert len(port.read_sizes) == 2
    assert max(port.read_sizes) <= 4096


def test_receive_accumulator_retains_next_log_fragment_between_requests():
    class FragmentPort(Port):
        def write(self, data):
            self.sent.append(json.loads(data))
            q = self.sent[-1]
            reply = dict(v=1, request_id=q['id'], base_mac=MAC, ok=True)
            prefix = b'' if len(self.sent) == 1 else b'complete\n'
            suffix = b'next log is ' if len(self.sent) == 1 else b''
            self.pending = [prefix + json.dumps(reply).encode() + b'\n' + suffix]
    port = FragmentPort()
    client = ConsoleClient('unused', MAC, serial_port=port)
    client.request('status')
    assert client._rx_buffer == b'next log is '
    client.request('status')
    assert client._rx_buffer == b''


@pytest.mark.parametrize('terminated', [False, True])
def test_oversized_serial_line_is_bounded_and_cleared(terminated):
    class OversizedPort(Port):
        def write(self, data):
            self.pending = [b'x'*32769 + (b'\n' if terminated else b'')]
    client = ConsoleClient('unused', MAC, serial_port=OversizedPort())
    with pytest.raises(ValueError, match='Oversized'):
        client.request('status')
    assert client._rx_buffer == b''


def test_unrelated_correlated_ids_are_skipped_before_current_reply():
    class CorrelationPort(Port):
        def write(self, data):
            super().write(data)
            unrelated = dict(v=1, request_id='previous', base_mac='00:11:22:33:44:55', ok=True)
            self.pending.insert(0, json.dumps(unrelated).encode()+b'\n')
    client = ConsoleClient('unused', MAC, serial_port=CorrelationPort())
    assert client.request('status')['base_mac'] == MAC


class SelectionClient:
    select_image = ConsoleClient.select_image
    def __init__(self, *, selected_name='known-good.bin', readback_name='known-good.bin', reboot=False):
        self.calls = []
        self.selected_name = selected_name
        self.readback_name = readback_name
        self.reboot = reboot
    def identify(self):
        return {'boot_id': BOOT}
    def request(self, op, **fields):
        self.calls.append((op, fields))
        if op == 'image_select':
            return dict(image=self.selected_name, image_sha256=IMAGE, file_sha256='c'*64)
        return dict(boot_id='2'*32 if self.reboot else BOOT, image=self.readback_name, image_sha256=IMAGE)


def test_select_existing_image_checks_readback_without_reupload():
    client = SelectionClient()
    result = client.select_image('known-good.bin')
    assert result['selected'] is True
    assert result['image_sha256'] == IMAGE
    assert [op for op, _ in client.calls] == ['image_select', 'status']
    assert client.calls[0][1]['name'] == 'known-good.bin'


@pytest.mark.parametrize('kwargs', [dict(selected_name='canary.bin'), dict(readback_name='canary.bin')])
def test_wrong_selected_image_never_reports_success(kwargs):
    with pytest.raises(ValueError, match='image'):
        SelectionClient(**kwargs).select_image('known-good.bin')


def test_reboot_during_selection_is_unverified():
    with pytest.raises(RuntimeError, match='rebooted'):
        SelectionClient(reboot=True).select_image('known-good.bin')


def test_invalid_select_path_is_rejected_before_device_request():
    client = SelectionClient()
    with pytest.raises(ValueError):
        client.select_image('../canary.bin')
    assert client.calls == []

@pytest.mark.parametrize('stored',[False,True])
def test_upload_recovers_lost_ack_by_manifest_bound_offset(tmp_path,monkeypatch,stored):
    from node_commissioner import console
    image=tmp_path/'node.bin';image.write_bytes(b'x'*512)
    monkeypatch.setattr(console,'verify_image',lambda *_:IMAGE)
    class Client:
        upload=ConsoleClient.upload
        def __init__(self):self.chunks=0;self.actual=0
        def identify(self):return dict(boot_id='a'*32,upload_status_supported=True)
        def request(self,op,**fields):
            if op=='image_chunk':
                self.chunks+=1
                if self.chunks==1:
                    self.actual=512 if stored else 0
                    raise TimeoutError('lost reply')
                self.actual=512;return dict(offset=512)
            if op=='image_status':return dict(boot_id='a'*32,active=True,name='node.bin',size=512,sha256='f'*64,offset=self.actual)
            if op=='image_end':return dict(image_sha256=IMAGE)
            return {}
    c=Client();assert c.upload(image,'f'*64)['bytes']==512
    assert c.chunks==(1 if stored else 2)


def test_upload_recovery_rejects_changed_console_boot(tmp_path,monkeypatch):
    from node_commissioner import console
    image=tmp_path/'node.bin';image.write_bytes(b'x'*512)
    monkeypatch.setattr(console,'verify_image',lambda *_:IMAGE)
    class Client:
        upload=ConsoleClient.upload
        def identify(self):return dict(boot_id='a'*32,upload_status_supported=True)
        def request(self,op,**fields):
            if op=='image_chunk':raise TimeoutError('lost reply')
            if op=='image_status':return dict(boot_id='b'*32,active=True,name='node.bin',size=512,sha256='f'*64,offset=512)
            return {}
    with pytest.raises(ValueError,match='upload session'):Client().upload(image,'f'*64)
