from setuptools import setup, find_packages
from distutils.extension import Extension

from os.path import join, dirname

packages = find_packages()

with open(join(dirname(__file__), 'version.txt'), 'r') as fileh:
    version = fileh.read().strip()

options = {'apk': {'window': None,
                   'requirements': 'sdl2,kivy,python3crystax==3.6,pygments,jedi',
                   'android-api': 19,
                   'ndk-dir': '/home/asandy/android/crystax-ndk-10.3.2',
                   'dist-name': 'pyonic_python3',
                   'ndk-version': '10.3.2',
                   'package': 'net.inclem.pyonicinterpreter3',
                   'permission': 'INTERNET',
                   'service': 'interpreter:interpreter_subprocess/interpreter.py',
                   # 'service': 'pip:interpreter_subprocess/interpreter.py',
                   # 'services': 'pip:interpreter_subprocess/interpreter.py;interpreter:interpreter_subprocess/interpreter.py',
                   'arch': 'armeabi-v7a',
                   'icon': 'build_assets/icon_py3-96.png',
                   'presplash': 'build_assets/presplash.png',
                   'whitelist': 'build_assets/whitelist.txt',
                   'local-recipes': './p4a_recipes',
                   # 'release': None,
                   # 'debug': None,
                   }}
setup(
    name='Pyonic Python 3 interpreter',
    version=version,
    description='A Python mobile IDE experiment',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=packages,
    options=options,
    package_data={'pyonic': ['*.py', '*.kv'],
                  'pyonic/interpreter_subprocess': ['*.py'],
                  'pyonic/assets': ['*.ttf', '*.txt'],
                  'pyonic/pydoc_data': ['*.py'],
                  # 'pyonic/distutils': ['*.py'],
                  # 'pyonic/distutils/command': ['*.py'],
                  'pyonic/osc': ['*.py']}
)
