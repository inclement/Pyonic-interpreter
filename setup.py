from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Distutils import build_ext

packages = find_packages()

options = {'apk': {'debug': None,
                   'requirements': 'sdl2,kivy',
                   'android-api': 19,
                   'ndk-dir': '/home/asandy/android/crystax-ndk-10.3.1',
                   'dist-name': 'pyde',
                   'ndk-version': '10.3.1',
                   'package': 'net.inclem.pyde',
                   'permission': 'INTERNET',
                   'service': 'interpreter:interpreter_subprocess/interpreter.py'
                   }}
setup(
    name='PyDE',
    version='0.1',
    description='A Python mobile IDE experiment',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=packages,
    options=options,
    package_data={'pyde': ['*.py', '*.kv'],
                  'pyde/interpreter_subprocess': ['*.py'],
                  'pyde/assets': ['*.ttf', '*.txt']}
)
