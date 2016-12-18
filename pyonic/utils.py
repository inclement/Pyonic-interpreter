from os import environ, path
import sys

###########################################
## _get_platform taken from kivy.utils

def _get_platform():
    # On Android sys.platform returns 'linux2', so prefer to check the
    # presence of python-for-android environment variables (ANDROID_ARGUMENT
    # or ANDROID_PRIVATE).
    if 'ANDROID_ARGUMENT' in environ:
        return 'android'
    elif environ.get('KIVY_BUILD', '') == 'ios':
        return 'ios'
    elif sys.platform in ('win32', 'cygwin'):
        return 'win'
    elif sys.platform == 'darwin':
        return 'macosx'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('freebsd'):
        return 'linux'
    return 'unknown'


platform = _get_platform()

###########################################


if platform == 'android':
    site_packages_path = '../pyonic_site-packages'
else:
    site_packages_path = path.join(path.abspath(path.dirname(__file__)), '..', 'pyonic_site-packages')

if site_packages_path not in sys.path:
    sys.path.insert(0, site_packages_path)

if platform == 'android':
    import site
    site.USER_SITE = '..'
    site.USER_BASE = site_packages_path
