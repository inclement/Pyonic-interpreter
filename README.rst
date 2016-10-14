PyDE
====

An experimental Python IDE for mobile devices, written in Python. PyDE
currently consists of a single interpreter window. Future targets
include support for multiple interpreters, different kinds of Python
tasks (app threads, background services), and editing/running Python
files.

PyDE uses `Kivy <https://kivy.org/#home>`__ for its gui, and runs on
Android using `python-for-android
<https://github.com/kivy/python-for-android>`__.

This is experimental software, with currently fairly limited
functionality and probably many bugs. Issue reports are welcome.

.. image:: pyde_android_small.png
    :width: 300px
    :alt: Example PyDE app use

Technical details
-----------------

PyDE runs as a Kivy application, starting a second process in the
background (a subprocess on desktop, a service on Android) to run the
Python code input. The output streams of this second process are
redirected to be formatted in Kivy labels in the main app.

This method seems quite crude, although it works well. An immediate
improvement will be to check how other similar projects do the same
thing.

It's currently very easy to break the app, e.g. with infinite loops or
by causing the second process to halt. Some of this can be fixed
(e.g. interrupt support for loops), but ultimately that's fine...it's
your interpreter to crash if you want!


TODO before release
-------------------

- fix message overloading with a queue
- disallow scrolling until screen full
