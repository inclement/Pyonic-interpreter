from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Distutils import build_ext

from os.path import join, dirname

packages = find_packages()

with open(join(dirname(__file__), 'version.txt'), 'r') as fileh:
    version = fileh.read().strip()

options = {'apk': {'window': None,
                   'requirements': 'sdl2,kivy,python2,pygments,jedi',
                   'android-api': 19,
                   'ndk-dir': '/home/asandy/android/crystax-ndk-10.3.2',
                   'dist-name': 'pyonic_python2',
                   'ndk-version': '10.3.2',
                   'package': 'net.inclem.pyonicinterpreter',
                   'permission': 'INTERNET',
                   'service': 'interpreter:interpreter_subprocess/interpreter.py',
                   # 'service': 'pip:interpreter_subprocess/interpreter.py',
                   # 'services': 'pip:interpreter_subprocess/interpreter.py;interpreter:interpreter_subprocess/interpreter.py',
                   'arch': 'armeabi-v7a',
                   'icon': 'build_assets/icon_py2-96.png',
                   'presplash': 'build_assets/presplash.png',
                   'whitelist': 'build_assets/whitelist.txt',
                   'local-recipes': './p4a_recipes',
                   # 'release': None,
                   # 'debug': None,
                   }}
setup(
    name='Pyonic Python 2 interpreter',
    version=version,
    description='A Python mobile IDE experiment',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=packages,
    options=options,
    package_data={'pyonic': ['*.py', '*.kv'],
                  'pyonic/interpreter_subprocess': ['*.py'],
                  'pyonic/assets': ['*.ttf', '*.txt']}
)
