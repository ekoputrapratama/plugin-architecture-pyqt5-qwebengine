
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout
from PyQt5.QtWebChannel import QWebChannel


from .WebView import MyWebView
from .usertypes import LoadEvent, Url
from .utils import Signal


class BrowserWindow(QWidget):
    app = None
    onClose = Signal()
    bridgeInitialized = False
    webview: MyWebView = None

    def __init__(self, application=None):
        super().__init__()
        from .MyApplication import MyApplication
        if application is not None and isinstance(application, MyApplication):
            self.app = application
            self.app.addWindow(self)

        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setMinimumSize(QSize(640, 480))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.channel = QWebChannel()

        self.webview = MyWebView(parent=self)
        self.webview.loadChanged.connect(self._loadChanged)
        self.layout.addWidget(self.webview)

    def _loadChanged(self, e):
        app = self.app
        if app is None:
            app = QApplication.instance()

        if e == LoadEvent.BEFORE_LOAD and not self.bridgeInitialized:
            self._initBridge()
            self.bridgeInitialized = True

        from .MyApplication import MyApplication
        if app is not None and isinstance(app, MyApplication):
            page = self.webview.page()
            if e == LoadEvent.BEFORE_LOAD:
                app.pluginManager.beforeLoad.emit(self.channel, page)
            elif e == LoadEvent.STARTED:
                app.pluginManager.loadStarted.emit(page)
            elif e == LoadEvent.FINISHED:
                app.pluginManager.loadFinished.emit(page)

    def _initBridge(self):
        print("Initializing web channel bridge...")
        page = self.webview.page()

        page.injectScript(":/qtwebchannel/qwebchannel.js", "QWebChannel API")

        app = self.app
        if app is None:
            app = QApplication.instance()

        # app is probably None in test
        from .MyApplication import MyApplication
        if app is not None and isinstance(app, MyApplication):
            app.pluginManager.bridgeInitialize.emit(page)

        page.setWebChannel(self.channel)

    def loadUrl(self, url: Url) -> None:
        if isinstance(url, QUrl):
            self.webview.setUrl(url)
        else:
            self.webview.setUrl(QUrl(url))

    def closeEvent(self, e):
        super().closeEvent(e)
        self.onClose.emit()
        # unregister our window from application
        if self.app is not None:
            self.app.removeWindow(self)
