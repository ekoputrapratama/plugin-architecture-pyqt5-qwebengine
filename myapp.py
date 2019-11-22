#!/usr/bin/env python3

"""Simple launcher for myapp."""
import myapp.myapp as myapp
import sys
import os

from PyQt5.QtCore import QProcess

RESTART_EXIT_CODE = 2

if __name__ == "__main__":
    exitCode = myapp.main()
    print("exit code", exitCode)

    if exitCode == RESTART_EXIT_CODE:
        proc = QProcess()
        proc.start(os.path.abspath(__file__))

    sys.exit(exitCode)
