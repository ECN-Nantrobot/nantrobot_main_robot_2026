#!/usr/bin/env python3

import json
import os
import socketserver
import threading
from typing import Any, TypedDict, cast


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 38765
MAX_STORED_EVENTS = 2000


class PinState(TypedDict):
    mode: str
    state: bool


class PinEvent(TypedDict):
    id: int
    event_type: str
    pin: int
    mode: str
    state: bool


class BackendState:

    def __init__(self):
        self._lock = threading.Lock()
        self.pins: dict[str, PinState] = {}
        self.events: list[PinEvent] = []
        self.next_event_id = 1

    def _default_pin_state(self) -> PinState:
        return {'mode': 'input', 'state': False}

    def _append_event(self, pin: int, event_type: str):
        pin_state = self.pins.setdefault(str(pin), self._default_pin_state())
        event: PinEvent = {
            'id': self.next_event_id,
            'event_type': event_type,
            'pin': pin,
            'mode': pin_state['mode'],
            'state': bool(pin_state['state']),
        }
        self.events.append(event)
        self.next_event_id += 1
        if len(self.events) > MAX_STORED_EVENTS:
            self.events = self.events[-MAX_STORED_EVENTS:]

    def initialize_state(self, pins: list[int]) -> dict[str, Any]:
        with self._lock:
            for pin in sorted(set(pins)):
                pin_key = str(pin)
                if pin_key not in self.pins:
                    self.pins[pin_key] = self._default_pin_state()
                    self._append_event(pin, 'pin_initialized')
            return {}

    def set_pin_mode(self, pin: int, mode: str) -> dict[str, Any]:
        if mode not in ('input', 'output'):
            raise ValueError('mode must be either input or output')

        with self._lock:
            pin_state = self.pins.setdefault(str(pin), self._default_pin_state())
            if pin_state['mode'] != mode:
                pin_state['mode'] = mode
                self._append_event(pin, 'pin_mode_changed')
            return {}

    def set_pin_state(self, pin: int, state: bool) -> dict[str, Any]:
        with self._lock:
            pin_state = self.pins.setdefault(str(pin), self._default_pin_state())
            next_state = bool(state)
            if bool(pin_state['state']) != next_state:
                pin_state['state'] = next_state
                self._append_event(pin, 'pin_state_changed')
            return {}

    def toggle_pin_if_input(self, pin: int) -> dict[str, Any]:
        with self._lock:
            pin_state = self.pins.setdefault(str(pin), self._default_pin_state())
            if pin_state['mode'] != 'input':
                return {'toggled': False, 'state': bool(pin_state['state'])}

            pin_state['state'] = not bool(pin_state['state'])
            self._append_event(pin, 'pin_state_toggled')
            return {'toggled': True, 'state': bool(pin_state['state'])}

    def get_pin_state(self, pin: int) -> dict[str, Any]:
        with self._lock:
            pin_state = self.pins.setdefault(str(pin), self._default_pin_state())
            return {
                'mode': pin_state['mode'],
                'state': bool(pin_state['state']),
            }

    def list_pins(self) -> dict[str, Any]:
        with self._lock:
            return {'pins': self.pins}

    def get_events_since(self, last_event_id: int) -> dict[str, Any]:
        with self._lock:
            events = [event for event in self.events if event['id'] > last_event_id]
            return {
                'events': events,
                'latest_event_id': self.next_event_id - 1,
            }

    def get_latest_event_id(self) -> dict[str, Any]:
        with self._lock:
            return {'latest_event_id': self.next_event_id - 1}

    def ping(self) -> dict[str, Any]:
        return {'alive': True}


BACKEND_STATE = BackendState()


class BackendTcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class BackendRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        raw_line = self.rfile.readline().decode('utf-8').strip()
        if not raw_line:
            return

        try:
            request_raw = json.loads(raw_line)
            if not isinstance(request_raw, dict):
                raise ValueError('invalid request payload')

            request = cast(dict[str, Any], request_raw)
            method = request.get('method')
            params_raw = request.get('params')
            params: dict[str, Any] = cast(dict[str, Any], params_raw) if isinstance(params_raw, dict) else {}
            if not isinstance(method, str):
                raise ValueError('invalid method')

            result = self._dispatch(method, params)
            response: dict[str, Any] = {
                'ok': True,
                'error': None,
                'result': result,
            }
        except Exception as exc:  # broad catch to keep daemon resilient
            response = {
                'ok': False,
                'error': str(exc),
                'result': {},
            }

        self.wfile.write((json.dumps(response) + '\n').encode('utf-8'))

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == 'ping':
            return BACKEND_STATE.ping()
        if method == 'initialize_state':
            pins = params.get('pins', [])
            if not isinstance(pins, list):
                raise ValueError('pins must be a list')
            parsed_pins = [int(pin) for pin in cast(list[Any], pins)]
            return BACKEND_STATE.initialize_state(parsed_pins)
        if method == 'set_pin_mode':
            return BACKEND_STATE.set_pin_mode(int(params['pin']), str(params['mode']))
        if method == 'set_pin_state':
            return BACKEND_STATE.set_pin_state(int(params['pin']), bool(params['state']))
        if method == 'toggle_pin_if_input':
            return BACKEND_STATE.toggle_pin_if_input(int(params['pin']))
        if method == 'get_pin_state':
            return BACKEND_STATE.get_pin_state(int(params['pin']))
        if method == 'list_pins':
            return BACKEND_STATE.list_pins()
        if method == 'get_events_since':
            return BACKEND_STATE.get_events_since(int(params.get('last_event_id', 0)))
        if method == 'get_latest_event_id':
            return BACKEND_STATE.get_latest_event_id()

        raise ValueError(f'unknown method: {method}')


def main():
    host = os.environ.get('NANTROBOT_GPIO_BACKEND_HOST', DEFAULT_HOST)
    port = int(os.environ.get('NANTROBOT_GPIO_BACKEND_PORT', str(DEFAULT_PORT)))
    with BackendTcpServer((host, port), BackendRequestHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
