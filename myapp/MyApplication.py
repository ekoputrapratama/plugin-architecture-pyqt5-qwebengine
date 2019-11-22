import os
import typing
import signal
from os import path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from .BrowserWindow import BrowserWindow
from .PluginManager import PluginManager
from .utils import Signal
from .config import config, Configuration

myapp = None


def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    # if QMessageBox.question(None, '', "Are you sure you want to quit?",
    #                         QMessageBox.Yes | QMessageBox.No,
    #                         QMessageBox.No) == QMessageBox.Yes:
    QApplication.quit()


def run(argsv):
    signal.signal(signal.SIGINT, sigint_handler)

    global myapp
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    myapp = MyApplication(argsv)
    myapp.setOrganizationName("MyOrganization")
    myapp.setApplicationName("MyApp")
    myapp.registerPluginDir(os.path.join(os.getcwd(), "plugins"))

    url = "file://" + os.path.join(os.getcwd(), "static", "index.html")
    window = BrowserWindow(myapp)
    window.loadUrl(url)
    # Python cannot handle signals while the Qt event loop is running.
    # so we need to use QTimer to let the interpreter run from time to time.
    # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    window.show()
    ret = myapp.exec_()
    return ret


class MyApplication(QApplication):
    windows: typing.List[BrowserWindow] = []
    windowAdded = Signal()
    windowRemoved = Signal()
    beforeRun = Signal()
    pluginsDirs: typing.List[str] = []
    pluginManager: PluginManager = None

    def __init__(self, argv, name="myapp"):
        super().__init__(argv)
        if config is None:
            self.config = Configuration(
                path.join(os.getcwd(), "{}.yml".format(name)))
        else:
            self.config = config

        self.pluginManager = PluginManager()

    def exec_(self):
        self.beforeRun.emit()
        return super().exec_()

    def registerPluginDir(self, directory: str) -> None:
        """Register directory as plugin base path directory"""
        if path.isabs(directory) and path.exists(directory):
            self.pluginManager.addPluginPath(directory)
        elif path.isabs(directory) and not path.exists(directory):
            print(
                "Plugin directory provided doesn't exists, trying to create the folder...")
            writable = os.access(path.dirname(directory), os.W_OK)
            if writable:
                os.makedirs(directory, 0o755, exist_ok=True)
                self.pluginManager.addPluginPath(directory)
            else:
                print(
                    "Plugin directory provided is not writable, ignoring it.")

    def addWindow(self, window: BrowserWindow) -> None:
        self.windows.append(window)
        self.windowAdded.emit(window)

    def removeWindow(self, window: BrowserWindow) -> None:
        self.windows.remove(window)
        self.windowRemoved.emit(window)
