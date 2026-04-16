#!/usr/bin/env python3

import os
import socket
import subprocess
import sys
import time
import json
from typing import Any, TypedDict, cast


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 38765


class PinState(TypedDict):
    mode: str
    state: bool


class PinEvent(TypedDict):
    id: int
    event_type: str
    pin: int
    mode: str
    state: bool


class RpcResponse(TypedDict):
    ok: bool
    error: str | None
    result: dict[str, Any]


def _backend_host() -> str:
    return os.environ.get('NANTROBOT_GPIO_BACKEND_HOST', DEFAULT_HOST)


def _backend_port() -> int:
    return int(os.environ.get('NANTROBOT_GPIO_BACKEND_PORT', str(DEFAULT_PORT)))


def parse_pin_list(pin_values: str) -> list[int]:
    pins: list[int] = []
    for value in pin_values.split(','):
        stripped_value = value.strip()
        if not stripped_value:
            continue
        pins.append(int(stripped_value))
    return sorted(set(pins))


def default_pins() -> list[int]:
    env_pins = os.environ.get('NANTROBOT_GPIO_EMULATOR_PINS', '')
    if env_pins.strip():
        return parse_pin_list(env_pins)
    return list(range(0, 28))


def _rpc_request(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'method': method,
        'params': params or {},
    }

    for attempt in range(2):
        try:
            return _send_rpc(payload)
        except OSError:
            if attempt == 0:
                _ensure_backend_running()
                continue
            raise

    raise RuntimeError('unreachable RPC retry state')


def _send_rpc(payload: dict[str, Any]) -> dict[str, Any]:
    host = _backend_host()
    port = _backend_port()

    with socket.create_connection((host, port), timeout=1.0) as sock:
        request_bytes = (json.dumps(payload) + '\n').encode('utf-8')
        sock.sendall(request_bytes)

        response_buffer = b''
        while b'\n' not in response_buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_buffer += chunk

    if not response_buffer:
        raise RuntimeError('empty backend response')

    response_line = response_buffer.split(b'\n', maxsplit=1)[0].decode('utf-8')
    response = _parse_response(response_line)
    if not response['ok']:
        raise RuntimeError(response['error'] or 'backend request failed')
    return response['result']


def _parse_response(raw_line: str) -> RpcResponse:
    raw_data = json.loads(raw_line)
    if not isinstance(raw_data, dict):
        return {'ok': False, 'error': 'invalid response payload', 'result': {}}

    raw = cast(dict[str, Any], raw_data)
    result_raw = raw.get('result')
    result = cast(dict[str, Any], result_raw) if isinstance(result_raw, dict) else {}
    error_raw = raw.get('error')

    return {
        'ok': bool(raw.get('ok', False)),
        'error': str(error_raw) if error_raw is not None else None,
        'result': result,
    }


def _ensure_backend_running():
    if _ping_backend():
        return

    cmd = [sys.executable, '-m', 'nantrobot_servers.gpio_emulator_backend_server']
    env = os.environ.copy()
    env['NANTROBOT_GPIO_BACKEND_HOST'] = _backend_host()
    env['NANTROBOT_GPIO_BACKEND_PORT'] = str(_backend_port())

    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )

    deadline = time.time() + 2.5
    while time.time() < deadline:
        if _ping_backend():
            return
        time.sleep(0.05)

    raise RuntimeError('failed to start GPIO backend server')


def _ping_backend() -> bool:
    try:
        _send_rpc({'method': 'ping', 'params': {}})
        return True
    except OSError:
        return False
    except RuntimeError:
        return False


def initialize_state(pin_numbers: list[int] | None = None):
    pins = default_pins() if pin_numbers is None else sorted(set(pin_numbers))
    _rpc_request('initialize_state', {'pins': pins})


def set_pin_mode(pin: int, mode: str):
    if mode not in ('input', 'output'):
        raise ValueError('mode must be either input or output')

    _rpc_request('set_pin_mode', {'pin': int(pin), 'mode': str(mode)})


def set_pin_state(pin: int, gpio_state: bool):
    _rpc_request('set_pin_state', {'pin': int(pin), 'state': bool(gpio_state)})


def toggle_pin_if_input(pin: int) -> tuple[bool, bool]:
    result = _rpc_request('toggle_pin_if_input', {'pin': int(pin)})
    return bool(result.get('toggled')), bool(result.get('state'))


def get_pin_state(pin: int) -> PinState:
    result = _rpc_request('get_pin_state', {'pin': int(pin)})
    return {
        'mode': 'output' if result.get('mode') == 'output' else 'input',
        'state': bool(result.get('state')),
    }


def list_pins() -> dict[int, PinState]:
    raw_result = _rpc_request('list_pins')
    raw_pins = raw_result.get('pins', {})
    if not isinstance(raw_pins, dict):
        return {}

    pins_dict = cast(dict[str, Any], raw_pins)

    result: dict[int, PinState] = {}
    for key, value in pins_dict.items():
        if not isinstance(value, dict):
            continue

        pin_number = int(key)
        value_dict = cast(dict[str, Any], value)
        result[pin_number] = {
            'mode': 'output' if value_dict.get('mode') == 'output' else 'input',
            'state': bool(value_dict.get('state')),
        }
    return result


def get_events_since(last_event_id: int) -> tuple[list[PinEvent], int]:
    raw = _rpc_request('get_events_since', {'last_event_id': int(last_event_id)})
    raw_events = raw.get('events', [])
    if not isinstance(raw_events, list):
        raw_events = []

    events: list[PinEvent] = []
    for item in cast(list[Any], raw_events):
        if not isinstance(item, dict):
            continue

        item_dict = cast(dict[str, Any], item)
        if not isinstance(item_dict.get('id'), int):
            continue
        if not isinstance(item_dict.get('event_type'), str):
            continue
        if not isinstance(item_dict.get('pin'), int):
            continue

        mode = 'output' if item_dict.get('mode') == 'output' else 'input'
        events.append(
            {
                'id': int(item_dict['id']),
                'event_type': str(item_dict['event_type']),
                'pin': int(item_dict['pin']),
                'mode': mode,
                'state': bool(item_dict.get('state')),
            }
        )

    latest_raw = raw.get('latest_event_id', last_event_id)
    latest_id = int(latest_raw) if isinstance(latest_raw, int) else int(last_event_id)
    return events, latest_id


def get_latest_event_id() -> int:
    raw = _rpc_request('get_latest_event_id')
    latest_raw = raw.get('latest_event_id', 0)
    return int(latest_raw) if isinstance(latest_raw, int) else 0
