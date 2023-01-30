import json
import sys
import time
from pynput import mouse, keyboard

from cheat import Cheat

config = {
    'offset_path': './data/csgo.json',

    'mouse_hotkey': {
        'trigger': 'x2',
        'aimbot': 'x1'
    },

    'keyboard_hotkey': {
        'exit': keyboard.Key.end,
        'glow': keyboard.Key.f1,
        'trigger': keyboard.Key.f2,
        'aimbot': keyboard.Key.f3
    },

    'function': {
        'exit': False,
        'glow': True,
        'trigger': False,
        'aimbot': False
    },

    'aimbot_fov': 10,
    'aimbot_head': True,
    'aimbot_friendly': False
}


def load_offset():
    with open(config['offset_path'], 'r') as f:
        return json.load(f)


def switch_function(name):
    config['function'][name] = not config['function'][name]


def mouse_on_click(x, y, button, pressed):
    for k, v in config['mouse_hotkey'].items():
        if button.name == v:
            switch_function(k)


def keyboard_on_press(key):
    for k, v in config['keyboard_hotkey'].items():
        if key == v:
            switch_function(k)


def register_hotkey():
    mouse.Listener(
        on_click=mouse_on_click
    ).start()
    keyboard.Listener(
        on_press=keyboard_on_press
    ).start()


def main():
    offset = load_offset()
    cheat = Cheat('csgo.exe', offset)
    cheat.connect()
    register_hotkey()

    while True:
        if config['function']['exit']:
            sys.exit(0)

        time.sleep(0.0025)

        if cheat.is_gaming():
            try:
                if config['function']['glow']:
                    cheat.glow_all_enemies()

                if config['function']['trigger']:
                    cheat.trigger()

                if config['function']['aimbot']:
                    cheat.aimbot(config['aimbot_fov'], config['aimbot_head'], config['aimbot_friendly'], config['aimbot_visible'])
            except Exception as e:
                print(f'[Error] {e}')


if __name__ == '__main__':
    main()
