import os
import re
import ast
import typing
import importlib
import configparser

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from .utils import Signal, findFiles
from .config import change_filter, getInstance


class PluginInfo(configparser.ConfigParser):
    def __init__(self, filepath):
        super().__init__()
        self._filepath = filepath
        self.read(self._filepath, encoding='utf-8')

    def isValid(self) -> bool:
        """"""
        return self.has_section("plugin") and self.has_option("plugin", "Module")


class PluginManager(QObject):
    pluginAdded = Signal()
    pluginRemoved = Signal()
    pluginActivated = Signal()
    pluginDeactivated = Signal()
    loadStarted = Signal()
    loadFinished = Signal()
    beforeLoad = Signal()
    bridgeInitialize = Signal()

    def __init__(self, pluginDirs: typing.List[str] = [], parent=None):
        super().__init__(parent)
        app = QApplication.instance()

        from .MyApplication import MyApplication
        assert isinstance(app, MyApplication)

        self._plugins = {}
        self._loadedPlugins = {}
        self._pluginsResources = {}
        self._pluginDirs = pluginDirs
        self.loadStarted.connect(self._loadStarted)
        self.beforeLoad.connect(self._beforeLoad)
        self.loadFinished.connect(self._loadFinished)
        self.bridgeInitialize.connect(self._bridgeInitialize)
        self._loadPlugins()

    def _bridgeInitialize(self, page):
        for name, resources in self._pluginsResources.items():
            for resource in resources:
                scriptName = name + "_" + os.path.basename(resource)

                if resource.endswith(".js"):
                    injectionPoint = QWebEngineScript.DocumentReady
                    page.injectScript(resource, scriptName, injectionPoint)
                elif resource.endswith(".css"):
                    injectionPoint = QWebEngineScript.DocumentReady
                    page.injectStylesheet(
                        resource, scriptName, injectionPoint)

    def _beforeLoad(self, channel, page):
        for name, plugin in self._plugins.items():
            if 'beforeLoad' in dir(plugin):
                plugin.beforeLoad(channel, page)
            elif 'before_load' in dir(plugin):
                plugin.before_load(channel, page)

    def _loadStarted(self, page):
        for name, plugin in self._plugins.items():
            if 'loadStarted' in dir(plugin):
                plugin.loadStarted(page)
            elif 'load_started' in dir(plugin):
                plugin.load_started(page)

    def _loadFinished(self, page):
        for name, plugin in self._plugins.items():
            if 'loadFinished' in dir(plugin):
                plugin.loadStarted(page)
            elif 'load_finished' in dir(plugin):
                plugin.load_started(page)

    def addPluginPath(self, path: str):
        assert os.path.isabs(path)
        if not path in self._pluginDirs:
            self._pluginDirs.append(path)
            self._loadPlugins()

    def _loadPlugin(self, pluginName):
        if pluginName in self._loadedPlugins.keys():
            return self._loadedPlugins[pluginName]

        identities_paths = []
        for directory in self._pluginDirs:
            identities_paths += findFiles("*.plugin", directory)

        module = None
        for f in identities_paths:
            info = PluginInfo(f)
            name = f
            if info.has_section("plugin") and info.has_option("plugin", "Name"):
                name = info.get("plugin", "Name")
            else:
                continue

            if name == pluginName:
                if not info.isValid():
                    print(f"Plugin identity {name} is not valid, please read documentation "
                          "about how to write plugin.")
                else:
                    parentdir = os.path.dirname(f)
                    module_path = os.path.join(
                        parentdir, info.get("plugin", "Module"))
                    if(not module_path.endswith(".py")):
                        module_path += ".py"

                    if os.path.exists(module_path):
                        try:
                            module_path = module_path
                            package = f"myapp.plugins.{name}"
                            spec = importlib.util.spec_from_file_location(
                                package, module_path)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            self._loadedPlugins[name] = module
                        except ImportError:
                            print(
                                f"Unable to load plugin module {name}")

                        break
                    else:
                        print(
                            f"module specified in {name} doesn't exists, it will be ignored.")

        return module

    def _loadPlugins(self):
        """"""
        identities_paths = []
        for directory in self._pluginDirs:
            identities_paths += findFiles("*.plugin", directory)

        plugins: typing.List[PluginInfo] = []

        for f in identities_paths:
            info = PluginInfo(f)
            name = f
            if info.has_section("plugin") and info.has_option("plugin", "Name"):
                name = info.get("plugin", "Name")

            # if it's already exists it means that user just add a new plugins directory
            if name in self._loadedPlugins.keys():
                continue

            if not info.isValid():
                print(f"Plugin identity {name} is not valid, please read documentation "
                      "about how to write plugin.")
            else:
                parentdir = os.path.dirname(f)
                module_path = os.path.join(
                    parentdir, info.get("plugin", "Module"))
                if(not module_path.endswith(".py")):
                    module_path += ".py"

                if os.path.exists(module_path):
                    info.set("plugin", "Path", module_path)
                    plugins.append(info)
                else:
                    print(
                        f"module specified in {f} doesn't exists, it will be ignored.")

        print(f"{len(plugins)} plugins found.")
        for plugin in plugins:
            try:
                name = plugin.get("plugin", "Name")

                module_path = plugin.get("plugin", "Path")
                package = f"myapp.plugins.{name}"
                spec = importlib.util.spec_from_file_location(
                    package, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._loadedPlugins[name] = module

                """
                By default plugin will be enabled if there was no plugin configuration.
                """
                cfg = getInstance().get(f"plugins.{name}")
                shouldLoad = True
                if cfg is None:
                    shouldLoad = False
                    cfg = dict()
                    cfg['enabled'] = True
                    getInstance().set(f"plugins.{name}.enabled", True)

                # if this is the first time the plugin is registered code above will trigger _pluginStateChange
                # and activate it, so we don't need to activate it again here
                if cfg['enabled'] and shouldLoad:
                    if 'activate' in dir(module):
                        module.activate()
                        self._plugins[name] = module

                if plugin.has_option("plugin", "Resources"):
                    resources = ast.literal_eval(
                        plugin.get("plugin", "Resources"))
                    base_path = os.path.dirname(module_path)

                    def to_abspath(path: str):
                        if not os.path.isabs(path):
                            return os.path.join(base_path, path)

                        return path

                    resources = list(map(to_abspath, resources))
                    self._pluginsResources[name] = resources

            except ImportError as e:
                name = plugin.get("plugin", "Name")
                print(
                    f"Unable to load plugin module {name} : ${e.msg}")

    @change_filter("plugins")
    def _pluginsStateChanged(self, key: str, value):
        """We only interested with the name and the value"""
        res = re.findall("plugins\\.(.*)\\.enabled", key)
        if key.endswith("enabled") and len(res) > 0:
            name = res[0]
            if not value:
                self.disablePlugin(name)
            elif value:
                self.enablePlugin(name)

    def enablePlugin(self, name: str):
        """"""
        print(f"enabling plugin {name}")
        if not name in self._plugins.keys():
            module = self._loadPlugin(name)
            if module is not None:
                if "activate" in dir(module):
                    module.activate()
                    self.pluginActivated.emit(name)
                    self._plugins[name] = module
                    self.pluginAdded.emit(name)
            else:
                print(f"Unable activate plugin {name}")

    def disablePlugin(self, name: str):
        """"""
        print(f"disabling plugin {name}")
        if name in self._plugins.keys():
            module = self._plugins[name]
            if "deactivate" in dir(module):
                module.deactivate()
                self.pluginDeactivated.emit(name)

            self._plugins.pop(name, None)
            self.pluginRemoved.emit(name)
