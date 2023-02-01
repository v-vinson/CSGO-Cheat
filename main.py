import json
import random
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
        'trigger': None,
        'aimbot': keyboard.Key.alt_l
    },

    'function': {
        'exit': False,
        'glow': True,
        'trigger': False,
        'aimbot': False,
    },

    'aimbot': {
        # 自瞄范围
        'fov': 20,

        # 锁头/锁身
        'lock_head': True,

        # 锁头率
        'lock_head_rate': 0.5,

        # 随机锁头锁身
        'lock_randomly': False,

        # 自动开枪
        'auto_fire': True,

        # 锁友军
        'friendly': False,

        # 仅锁可见
        'visible': False,

        # 平滑度（0~1，越大越平滑）
        'smooth': 0.7
    }
}


def load_offset():
    with open(config['offset_path'], 'r') as f:
        return json.load(f)


def switch_function(name):
    config['function'][name] = not config['function'][name]

    if name == 'aimbot' and config['aimbot']['lock_randomly']:
        config['aimbot']['lock_head'] = random.random() < config['aimbot']['lock_head_rate']


def enable_function(name):
    if not config['function'][name]:
        switch_function(name)


def disable_function(name):
    if config['function'][name]:
        switch_function(name)


def mouse_on_click(x, y, button, pressed):
    for k, v in config['mouse_hotkey'].items():
        if button.name == v:
            switch_function(k)


def keyboard_on_press(key):
    for k, v in config['keyboard_hotkey'].items():
        if hasattr(key, 'char'):
            if key.char == v:
                enable_function(k)
        else:
            if key == v:
                enable_function(k)


def keyboard_on_release(key):
    for k, v in config['keyboard_hotkey'].items():
        if hasattr(key, 'char'):
            if key.char == v:
                disable_function(k)
        else:
            if key == v:
                disable_function(k)


def register_hotkey():
    mouse.Listener(
        on_click=mouse_on_click
    ).start()
    keyboard.Listener(
        on_press=keyboard_on_press,
        on_release=keyboard_on_release
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
                    cheat.aimbot(config['aimbot']['fov'],
                                 config['aimbot']['lock_head'],
                                 config['aimbot']['auto_fire'],
                                 config['aimbot']['friendly'],
                                 config['aimbot']['visible'],
                                 config['aimbot']['smooth'])

            except Exception as e:
                print(f'[Error] {e}')


if __name__ == '__main__':
    main()
