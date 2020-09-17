#!/usr/bin/env python3

import gettext
gettext.install('wcg', './locales')

import sys
print(sys.argv[0])

from wx import App
from gui import MainFrame


if __name__ == '__main__':
    app = App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()

