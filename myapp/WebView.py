from PyQt5.QtCore import QFile
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from .usertypes import LoadEvent, Url
from .utils import Signal


class MyWebView(QWebEngineView):
    loadChanged = Signal(LoadEvent)

    def __init__(self, parent):
        super().__init__(parent)
        self.loadStarted.connect(self._loadStarted)
        self.loadFinished.connect(self._loadFinished)

        page = MyWebPage(profile=None, parent=self)
        self.setPage(page)

    def _loadStarted(self):
        self.contentLoaded = False
        self.loadChanged.emit(LoadEvent.STARTED)

    def _loadFinished(self):
        self.contentLoaded = True
        self.loadChanged.emit(LoadEvent.FINISHED)

    def load(self, url):
        self.setUrl(url)

    def setUrl(self, url):
        self.loadChanged.emit(LoadEvent.BEFORE_LOAD)
        return super().setUrl(url)


def _createWebengineScript(path: Url, name: str, injectionPoint=None, isStylesheet: bool = False) -> QWebEngineScript:

    if injectionPoint is None:
        injectionPoint = QWebEngineScript.DocumentCreation

    script = QWebEngineScript()
    script_file = QFile(path)

    if script_file.open(QFile.ReadOnly):
        script_string = str(script_file.readAll(), 'utf-8')
        script.setInjectionPoint(injectionPoint)
        script.setName(name)
        script.setRunsOnSubFrames(True)
        script.setWorldId(QWebEngineScript.MainWorld)
        if isStylesheet:
            source = ("(function(){"
                      ""
                      "const css = document.createElement('style');\n"
                      "css.type = 'text/css';\n"
                      "css.innerText = `" + script_string.strip() + "`\n"
                      "document.head.appendChild(css);\n"
                      "})()")
            script.setSourceCode(source)
        else:
            script.setSourceCode(script_string)

    return script


class MyWebPage(QWebEnginePage):

    def __init__(self, profile, parent):
        super().__init__(profile, parent)

    def injectScript(self, path: Url, name: str, injectionPoint=None):
        """Inject javascript to a web page."""
        script = _createWebengineScript(path, name, injectionPoint, False)
        self.scripts().insert(script)

    def injectStylesheet(self, path: Url, name: str, injectionPoint=None):
        """Inject stylesheet to a web page."""
        script = _createWebengineScript(path, name, injectionPoint, True)
        self.scripts().insert(script)
