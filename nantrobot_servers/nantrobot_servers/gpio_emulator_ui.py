#!/usr/bin/env python3

import argparse
import tkinter as tk
from typing import TypedDict

from . import gpio_emulator_backend as backend


class RowWidgets(TypedDict):
    mode_button: tk.Button
    state_button: tk.Button


class PinSpec(TypedDict):
    physical: int
    label: str
    bcm: int | None
    controllable: bool


def _gpio(physical: int, bcm: int, label: str = '') -> PinSpec:
    signal = f'GPIO{bcm}' if not label else f'GPIO{bcm} {label}'
    return {
        'physical': physical,
        'label': signal,
        'bcm': bcm,
        'controllable': True,
    }


def _fixed(physical: int, label: str) -> PinSpec:
    return {
        'physical': physical,
        'label': label,
        'bcm': None,
        'controllable': False,
    }


PINOUT_PAIRS: list[tuple[PinSpec, PinSpec]] = [
    (_fixed(1, '3V3'), _fixed(2, '5V')),
    (_gpio(3, 2), _fixed(4, '5V')),
    (_gpio(5, 3), _fixed(6, 'GND')),
    (_gpio(7, 4), _gpio(8, 14)),
    (_fixed(9, 'GND'), _gpio(10, 15)),
    (_gpio(11, 17), _gpio(12, 18)),
    (_gpio(13, 27), _fixed(14, 'GND')),
    (_gpio(15, 22), _gpio(16, 23)),
    (_fixed(17, '3V3'), _gpio(18, 24)),
    (_gpio(19, 10), _fixed(20, 'GND')),
    (_gpio(21, 9), _gpio(22, 25)),
    (_gpio(23, 11), _gpio(24, 8)),
    (_fixed(25, 'GND'), _gpio(26, 7)),
    (_fixed(27, 'ID_SD'), _fixed(28, 'ID_SC')),
    (_gpio(29, 5), _fixed(30, 'GND')),
    (_gpio(31, 6), _gpio(32, 12)),
    (_gpio(33, 13), _fixed(34, 'GND')),
    (_gpio(35, 19), _gpio(36, 16)),
    (_gpio(37, 26), _gpio(38, 20)),
    (_fixed(39, 'GND'), _gpio(40, 21)),
]


PALETTE = {
    'app_bg': '#eef2f7',
    'panel_bg': '#f7f9fc',
    'header_bg': '#17324d',
    'header_text': '#f5f8ff',
    'title_text': '#ffffff',
    'subtitle_text': '#d3dfef',
    'legend_text': '#4b5f77',
    'chip_bg': '#ffffff',
    'chip_border': '#d7e0ec',
    'state_high': '#11a36b',
    'state_low': '#9aa9bd',
    'state_fg': '#ffffff',
    'mode_input_bg': '#2d7ff2',
    'mode_output_bg': '#c16b18',
    'button_fg': '#ffffff',
    'button_disabled_bg': '#d9e1ed',
    'button_disabled_fg': '#8a96a8',
    'placeholder_bg': '#eef3f9',
    'placeholder_fg': '#73839a',
}


class GpioEmulatorUi:

    def __init__(self, pins: list[int]):
        self.enabled_pins = set(pins)
        self.controllable_pins = sorted(
            pin_spec['bcm']
            for pin_pair in PINOUT_PAIRS
            for pin_spec in pin_pair
            if pin_spec['controllable'] and pin_spec['bcm'] is not None and pin_spec['bcm'] in self.enabled_pins
        )

        backend.initialize_state(self.controllable_pins)

        self.root = tk.Tk()
        self.root.title('Nantrobot GPIO Emulator')
        self.root.geometry('1080x600')
        self.root.configure(bg=PALETTE['app_bg'])

        header_frame = tk.Frame(self.root, bg=PALETTE['header_bg'], padx=18, pady=16)
        header_frame.pack(fill=tk.X, padx=16, pady=(14, 8))

        title = tk.Label(
            header_frame,
            text='GPIO Emulator',
            font=('Helvetica', 19, 'bold'),
            bg=PALETTE['header_bg'],
            fg=PALETTE['title_text'],
        )
        title.pack(anchor='w')

        subtitle = tk.Label(
            header_frame,
            text='Raspberry Pi header layout - toggle mode/state on controllable GPIO pins',
            font=('Helvetica', 10),
            bg=PALETTE['header_bg'],
            fg=PALETTE['subtitle_text'],
            pady=2,
        )
        subtitle.pack(anchor='w')

        legend = tk.Label(
            header_frame,
            text='State icons:  ● active   ○ inactive (click state icon to toggle in input mode)',
            font=('Helvetica', 9),
            bg=PALETTE['header_bg'],
            fg=PALETTE['subtitle_text'],
            pady=2,
        )
        legend.pack(anchor='w')

        panel = tk.Frame(
            self.root,
            bg=PALETTE['panel_bg'],
            padx=14,
            pady=12,
            highlightbackground=PALETTE['chip_border'],
            highlightthickness=1,
        )
        panel.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        self.table_frame = tk.Frame(panel, bg=PALETTE['panel_bg'])
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        self.widgets: dict[int, RowWidgets] = {}
        self._build_header()
        self._build_rows()
        self.last_event_id = backend.get_latest_event_id()
        self._refresh_all_visible_pins()
        self._fit_window_height_to_content()
        self._schedule_refresh()

    def _fit_window_height_to_content(self):
        self.root.update_idletasks()

        requested_width = max(1080, self.root.winfo_reqwidth())
        requested_height = self.root.winfo_reqheight() + 8

        screen_height = self.root.winfo_screenheight()
        max_height = max(600, screen_height - 80)
        target_height = min(requested_height, max_height)

        self.root.geometry(f'{requested_width}x{target_height}')
        self.root.minsize(980, min(target_height, 600))

    def _build_header(self):
        headers = ['PHYS', 'SIGNAL', 'MODE', 'STATE', '', 'STATE', 'MODE', 'SIGNAL', 'PHYS']
        for index, header in enumerate(headers):
            label = tk.Label(
                self.table_frame,
                text=header,
                font=('Helvetica', 10, 'bold'),
                padx=10,
                pady=6,
                bg=PALETTE['panel_bg'],
                fg=PALETTE['legend_text'],
            )
            label.grid(row=0, column=index, sticky='w')

    def _build_rows(self):
        for row, (left_pin, right_pin) in enumerate(PINOUT_PAIRS, start=1):
            self._build_pin(row, left_pin, is_left=True)

            separator = tk.Label(
                self.table_frame,
                text='• •',
                font=('Helvetica', 11, 'bold'),
                padx=8,
                pady=4,
                bg=PALETTE['panel_bg'],
                fg='#95a6bc',
            )
            separator.grid(row=row, column=5)

            self._build_pin(row, right_pin, is_left=False)

    def _build_pin(self, row: int, pin_spec: PinSpec, is_left: bool):
        if is_left:
            phys_col, signal_col, mode_col, state_col = 0, 1, 2, 3
        else:
            state_col, mode_col, signal_col, phys_col = 5, 6, 7, 8

        color = self._signal_color(pin_spec)
        phys_label = tk.Label(
            self.table_frame,
            text=str(pin_spec['physical']),
            width=5,
            bg=color,
            fg='#213448',
            relief=tk.FLAT,
            padx=4,
            pady=4,
        )
        phys_label.grid(row=row, column=phys_col, padx=2, pady=2)

        signal_label = tk.Label(
            self.table_frame,
            text=pin_spec['label'],
            width=14,
            bg=color,
            fg='#213448',
            padx=6,
            pady=4,
            anchor='w',
        )
        signal_label.grid(row=row, column=signal_col, padx=2, pady=2, sticky='w')

        bcm_pin = pin_spec['bcm']
        can_control = pin_spec['controllable'] and bcm_pin is not None and bcm_pin in self.enabled_pins
        if can_control and bcm_pin is not None:
            self._build_controls(row, mode_col, state_col, bcm_pin)
            return

        self._build_placeholders(row, mode_col, state_col)

    def _build_controls(self, row: int, mode_col: int, state_col: int, bcm_pin: int):
        mode_button = tk.Button(
            self.table_frame,
            text='INPUT',
            width=10,
            bd=0,
            relief=tk.FLAT,
            fg=PALETTE['button_fg'],
            activeforeground=PALETTE['button_fg'],
            bg=PALETTE['mode_input_bg'],
            activebackground=PALETTE['mode_input_bg'],
            command=lambda pin_number=bcm_pin: self._toggle_mode(pin_number),
        )
        mode_button.grid(row=row, column=mode_col, padx=2, pady=2)

        state_button = tk.Button(
            self.table_frame,
            text='○',
            width=7,
            bd=0,
            relief=tk.FLAT,
            padx=4,
            pady=4,
            bg=PALETTE['state_low'],
            fg=PALETTE['state_fg'],
            activeforeground=PALETTE['state_fg'],
            activebackground=PALETTE['state_low'],
            font=('Helvetica', 12, 'bold'),
            command=lambda pin_number=bcm_pin: self._toggle_input(pin_number),
        )
        state_button.grid(row=row, column=state_col, padx=2, pady=2)

        self.widgets[bcm_pin] = {
            'mode_button': mode_button,
            'state_button': state_button,
        }

    def _build_placeholders(self, row: int, mode_col: int, state_col: int):
        mode_label = tk.Label(
            self.table_frame,
            text='N/A',
            width=10,
            padx=2,
            pady=4,
            fg=PALETTE['placeholder_fg'],
            bg=PALETTE['placeholder_bg'],
            relief=tk.FLAT,
        )
        mode_label.grid(row=row, column=mode_col, padx=2, pady=2)

        state_label = tk.Label(
            self.table_frame,
            text='•',
            width=7,
            padx=4,
            pady=4,
            fg=PALETTE['placeholder_fg'],
            bg=PALETTE['placeholder_bg'],
            font=('Helvetica', 12, 'bold'),
        )
        state_label.grid(row=row, column=state_col, padx=2, pady=2)

    def _signal_color(self, pin_spec: PinSpec) -> str:
        label = pin_spec['label']
        if pin_spec['controllable']:
            return '#dbeaff'
        if label == 'GND':
            return '#d4d9e2'
        if label in ('3V3', '5V'):
            return '#ffd9d8'
        return '#f2ead0'

    def _toggle_mode(self, pin: int):
        current_mode = backend.get_pin_state(pin)['mode']
        next_mode = 'output' if current_mode == 'input' else 'input'
        backend.set_pin_mode(pin, next_mode)
        self._refresh_pin(pin)

    def _toggle_input(self, pin: int):
        backend.toggle_pin_if_input(pin)
        self._refresh_pin(pin)

    def _refresh_pin(self, pin: int):
        pin_state = backend.get_pin_state(pin)
        mode = pin_state['mode']
        gpio_state = pin_state['state']

        mode_text = 'INPUT' if mode == 'input' else 'OUTPUT'
        state_icon = '●' if gpio_state else '○'
        state_bg = PALETTE['state_high'] if gpio_state else PALETTE['state_low']

        widgets = self.widgets[pin]
        if mode == 'input':
            mode_bg = PALETTE['mode_input_bg']
        else:
            mode_bg = PALETTE['mode_output_bg']

        widgets['mode_button'].config(
            text=mode_text,
            bg=mode_bg,
            activebackground=mode_bg,
        )
        widgets['state_button'].config(
            text=state_icon,
            bg=state_bg,
            activebackground=state_bg,
        )

        if mode == 'input':
            widgets['state_button'].config(
                state=tk.NORMAL,
                fg=PALETTE['state_fg'],
                activeforeground=PALETTE['state_fg'],
                cursor='hand2',
            )
        else:
            widgets['state_button'].config(
                state=tk.DISABLED,
                fg=PALETTE['state_fg'],
                disabledforeground=PALETTE['button_disabled_fg'],
                cursor='arrow',
            )

    def _schedule_refresh(self):
        events, latest_event_id = backend.get_events_since(self.last_event_id)
        self.last_event_id = latest_event_id

        changed_pins = {
            event['pin']
            for event in events
            if event['pin'] in self.widgets
        }

        for pin in changed_pins:
            self._refresh_pin(pin)

        self.root.after(300, self._schedule_refresh)

    def _refresh_all_visible_pins(self):
        for pin in self.controllable_pins:
            if pin in self.widgets:
                self._refresh_pin(pin)

    def run(self):
        self.root.mainloop()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='GPIO emulator UI for action-server testing')
    parser.add_argument(
        '--pins',
        type=str,
        default=None,
        help='Comma-separated list of GPIO pins to emulate. Defaults to env pins or 0..27.',
    )
    # launch_ros injects extra arguments (e.g. --ros-args ...); ignore unknown args here.
    args, _unknown_args = parser.parse_known_args()
    return args


def main():
    args = _parse_args()
    if args.pins:
        pins = backend.parse_pin_list(args.pins)
    else:
        pins = backend.default_pins()

    app = GpioEmulatorUi(pins)
    app.run()


if __name__ == '__main__':
    main()
