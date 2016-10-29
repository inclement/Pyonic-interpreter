from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Distutils import build_ext

packages = find_packages()

options = {'apk': {'window': None,
                   'requirements': 'sdl2,kivy,python3crystax,pygments',
                   'android-api': 19,
                   'ndk-dir': '/home/asandy/android/crystax-ndk-10.3.2',
                   'dist-name': 'pyonic',
                   'ndk-version': '10.3.2',
                   'package': 'net.inclem.pyonicinterpreter3',
                   'permission': 'INTERNET',
                   'service': 'interpreter:interpreter_subprocess/interpreter.py',
                   'arch': 'armeabi-v7a',
                   'icon': 'build_assets/icon_py3-96.png',
                   'presplash': 'build_assets/presplash.png',
                   # 'release': None,
                   #'debug': None,
                   }}
setup(
    name='Pyonic Python 3 interpreter',
    version='0.7',
    description='A Python mobile IDE experiment',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=packages,
    options=options,
    package_data={'pyonic': ['*.py', '*.kv'],
                  'pyonic/interpreter_subprocess': ['*.py'],
                  'pyonic/assets': ['*.ttf', '*.txt']}
)
