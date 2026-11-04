import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('survey_bridge', Path(__file__).resolve().parents[2]/'survey-simulator/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
ROW = dict(label='A1', dhcp_reservation_mac='00:11:22:33:44:55')


class Device:
    def __init__(self, version='0.10.1'):
        self.status = dict(label='A1', base_mac=ROW['dhcp_reservation_mac'], firmware=version,
                           panel=dict(source='scripted_mission_shared_world', survey=dict(active=False)))
        self.writes = []

    def request(self, method, path, body=None, **kwargs):
        if method == 'GET':
            return self.status
        packet = json.loads(body)
        self.writes.append(packet)
        self.status['panel'] = dict(source='host_fictional_survey', survey=dict(active=True, run=packet['run']))
        return dict(ok=True)


def packet(seq=1, run=100):
    return dict(n=0, op='display_survey', run=run, seq=seq)


@pytest.mark.parametrize('version', ['0.10.0', '0.10.1'])
def test_supported_firmware_and_latest_only_delivery(version):
    device = Device(version)
    target = bridge.BridgeTarget(ROW, device)
    target.deliver(packet()); target.deliver(packet()); target.deliver(packet(2))
    assert len(device.writes) == 2
    assert target.report['verified']


@pytest.mark.parametrize('change', [dict(firmware='0.10.2'), dict(label='B1'), dict(base_mac='wrong')])
def test_unknown_firmware_or_identity_never_writes(change):
    device = Device(); device.status.update(change)
    with pytest.raises(ValueError):
        bridge.BridgeTarget(ROW, device).deliver(packet())
    assert not device.writes


def test_observed_mode_change_yields_until_explicit_restart():
    device = Device(); target = bridge.BridgeTarget(ROW, device)
    target.deliver(packet())
    device.status['panel']['source'] = 'scripted_mission_shared_world'
    target.deliver(packet(2))
    assert target.report['yielded'] and len(device.writes) == 1
    device.status['panel']['source'] = 'host_fictional_survey'
    target.deliver(packet(3))
    assert len(device.writes) == 1


def test_session_reset_is_allowed_but_another_run_yields():
    device = Device(); target = bridge.BridgeTarget(ROW, device)
    target.deliver(packet()); target.deliver(packet(2, run=101))
    assert len(device.writes) == 2
    device.status['panel']['survey']['run'] = 999
    target.deliver(packet(3, run=101))
    assert target.report['yielded'] and len(device.writes) == 2


def test_local_node_lock_is_exclusive_and_released(tmp_path):
    with bridge.node_lock(ROW['dhcp_reservation_mac'], tmp_path):
        with pytest.raises(ValueError, match='Another local bridge'):
            with bridge.node_lock(ROW['dhcp_reservation_mac'], tmp_path):
                pass
    with bridge.node_lock(ROW['dhcp_reservation_mac'], tmp_path):
        pass


def test_uncertain_first_write_does_not_reclaim_a_different_controller():
    device = Device()
    request = device.request
    def uncertain(method, path, body=None, **kwargs):
        result = request(method, path, body, **kwargs)
        if method == 'POST':
            raise TimeoutError()
        return result
    device.request = uncertain
    target = bridge.BridgeTarget(ROW, device)
    with pytest.raises(TimeoutError):
        target.deliver(packet())
    device.status['panel']['survey']['run'] = 999
    target.deliver(packet(2))
    assert target.report['yielded'] and len(device.writes) == 1
