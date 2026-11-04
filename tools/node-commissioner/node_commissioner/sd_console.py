"""SD maintenance transport through the identified LilyGo ESP-NOW relay."""
import json
import re
import time

PHASES = ['IDLE','INSPECTING','READY','FORMATTING','WRITING','READING','PASSED','FAILED','INTERRUPTED']
ERRORS = ['', 'card_not_responding', 'card_changed', 'unsupported_geometry', 'filesystem_driver_unavailable', 'format_buffer_unavailable', 'format_or_mbr_verification_failed', 'test_directory_failed', 'invalid_file_count', 'test_create_failed', 'test_close_failed', 'invalid_test_extent', 'test_buffer_unavailable', 'test_open_failed', 'test_file_size_changed', 'test_read_failed', 'test_write_failed', 'test_data_mismatch', 'test_sync_failed', 'test_cleanup_failed', 'cannot_record_destructive_intent', 'format_or_test_failed', 'cannot_record_result', 'power_loss_or_restart']


def decode_report(raw):
    if not isinstance(raw, str) or not re.fullmatch('[0-9a-f]{288}', raw):
        raise ValueError('Invalid SD report length/encoding')
    p=bytes.fromhex(raw)
    if p[0]>6 or p[1]!=1 or p[2]>=len(PHASES) or p[3]&~31:
        raise ValueError('Unsupported SD report')
    u32=lambda n:int.from_bytes(p[n:n+4],'little')
    u64=lambda n:int.from_bytes(p[n:n+8],'little')
    flags=p[3];phase=PHASES[p[2]];identity=p[16:56];card=identity.hex()
    filesystem='FAT32' if flags&2 else 'UNSUPPORTED' if u32(12)==0 else 'UNMOUNTABLE'
    sd=dict(maintenance_supported=bool(flags&16),state='PASS' if flags&4 else 'TESTING' if phase in ('FORMATTING','WRITING','READING') else 'UNRESPONSIVE' if not flags&1 else 'READY' if flags&2 else filesystem,presence='RESPONDING' if flags&1 else 'UNKNOWN',autoformat=False,probe_error_code=u32(8),fatfs_result=u32(12),destructive_scope='entire_node_sd_card_MBR_and_FAT32')
    if flags&1:
        sd.update(card_id=card,sector_bytes=int.from_bytes(identity[28:32],'big'),card_serial=int.from_bytes(identity[16:20],'big'),capacity_bytes=u64(72),filesystem_bytes=u64(80),free_bytes=u64(88),filesystem=filesystem,isolated_read_write='PASS' if flags&4 else 'PENDING')
    sd['test']=dict(job=u32(4),phase=phase,mode='full' if flags&8 else 'quick',target_bytes=u64(96),written_bytes=u64(104),read_bytes=u64(112),write_ms=u32(120),read_ms=u32(124),failed_offset=u64(128),error=ERRORS[p[140]] if p[140]<len(ERRORS) else 'unknown_storage_error',capacity_verification='USABLE_DATA_EXTENT_PASSED' if phase=='PASSED' and flags&8 else 'NOT_VERIFIED',reboot_persistent=True)
    if u32(136) and phase=='READY':sd.update(format_token=p[56:72].hex(),permit_remaining_ms=u32(136))
    return p[0],sd


class ConsoleSdClient:
    def __init__(self,console,mac,label):
        self.console,self.mac,self.label=console,mac,label
        self.health={}

    def request(self,method,path,body=b'',**kwargs):
        if method=='GET' and path=='/v1/status':
            action=0;fields={}
            # Opening USB can reboot the console. Wait for a new authenticated
            # health poll on that same connection before using its roster entry.
            for attempt in range(30):
                status=self.console.request('status')
                node=next((n for n in status.get('nodes',[]) if n.get('label')==self.label),None)
                if not node or node.get('mac')!=self.mac or not node.get('registered'):
                    raise ValueError('Console has no matching registered node')
                if node.get('observed') and node.get('age_ms',90000)<15000:
                    break
                time.sleep(1)
            else:
                raise ValueError('Console has no fresh identified observation for this node')
            self.health=node
        elif method=='POST' and path=='/v1/control':
            command=json.loads(body)
            action={'sd_prepare':1,'sd_format_quick':2,'sd_format_full':3}.get(command.get('op'))
            if action is None:raise ValueError('Unsupported relay command')
            fields={k:command[k] for k in ('card_id','token') if k in command}
        else:raise ValueError('Unsupported relay operation')
        accepted=self.console.request('sd_request',label=self.label,action=action,**fields)
        transaction=accepted.get('transaction','')
        if accepted.get('node_mac')!=self.mac or not re.fullmatch('[0-9a-f]{32}',transaction):
            raise ValueError('Wrong relay target or transaction')
        for _ in range(40):
            time.sleep(.2)
            result=self.console.request('sd_result',transaction=transaction)
            if result.get('node_mac')!=self.mac:raise ValueError('Relay target changed')
            if result.get('timed_out'):raise TimeoutError('Node did not answer SD request')
            if not result.get('complete'):continue
            code,sd=decode_report(result.get('report_hex'))
            if code:raise ValueError(f'Node rejected SD operation (code {code})')
            if action:return dict(ok=True,job=sd['test']['job'])
            return dict(v=1,type='status',base_mac=self.mac,label=self.label,boot_count=self.health.get('boots'),firmware=self.health.get('version'),app_sha256=self.health.get('image_sha256'),transport='lilygo_espnow',sd=sd)
        raise TimeoutError('Relay completion not observed')
