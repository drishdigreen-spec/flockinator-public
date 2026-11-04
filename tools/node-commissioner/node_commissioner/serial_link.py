import time
import uuid
import serial
from .protocol import encode_request, decode_response, validate_status


class SerialLink:
    def __init__(self, port: str, mac: str):
        self.mac = mac
        self.serial = serial.Serial(port=None, baudrate=115200, timeout=0.2, write_timeout=2)
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = port
        self.serial.open()

    def close(self):
        self.serial.close()

    def request(self, op: str = "status", timeout: float = 8, **fields) -> dict:
        request_id = uuid.uuid4().hex
        self.serial.write(encode_request(op, request_id, self.mac, **fields))
        deadline = time.monotonic() + timeout
        data = bytearray()
        while time.monotonic() < deadline:
            chunk = self.serial.read_until(b"\n", 32769 - len(data))
            data.extend(chunk)
            if len(data) > 32768:
                raise ValueError("Oversized device response")
            if not data.endswith(b"\n"):
                continue
            result = decode_response(bytes(data), request_id)
            data.clear()
            if result is None:
                continue
            validate_status(result, self.mac)
            if result.get("ok") is not True:
                raise ValueError(f"Device rejected request: {result.get('error', 'unknown')}")
            return result
        raise TimeoutError(f"No matching {op} response from {self.mac}")
