
from pythonforandroid.toolchain import PythonRecipe


class PipRecipe(PythonRecipe):
    # version = 'master'
    version = '9.0.1'
    url = 'https://github.com/pypa/pip/archive/{version}.tar.gz'

    # depends = [('python2', 'python3crystax'), 'setuptools']
    depends = [('python2', 'python3crystax')]

    call_hostpython_via_targetpython = False

    patches = ['fix_android_detection.patch']
    # pip detects Android as Linux, but crashes trying to find the
    # distro with subprocess


recipe = PipRecipe()
