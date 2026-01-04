import importlib.util
import sys
from pathlib import Path
from typing import List

from src.core.plugin_manager.plugin_api import PluginBase, API_VERSION
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import PLUGIN_DIR


logger  = OmixForgeLogger.get_logger()

class PluginManager:

    def __init__(self):
        self.plugins_dir = self.get_plugins_dir()
        self.loaded_plugins: List[PluginBase] = []

        self.plugins = {}

    def discover_plugin_files(self):
        return list(self.plugins_dir.glob("*.py"))

    def load_all(self, window):
        self.window = window
        self.plugins_page = window.plugins_page

        for file in self.discover_plugin_files():
            try:
                plugin = self._load_plugin_file(file)

                if plugin.api_version() != API_VERSION:
                    logger.warning(f"Plugin {plugin.name()} incompatible API")
                    continue

                plugin.load(window, self.plugins_page)

                self.plugins[plugin.name()] = plugin

                window.add_plugin_sidebar_item(plugin.name())

                self.loaded_plugins.append(plugin)

                logger.info(f"Loaded plugin: {plugin.name()}")

            except Exception as e:
                logger.error(f"Failed loading {file.name}: {e}")


    def _load_plugin_file(self, path: Path) -> PluginBase:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)

        plugin_class = getattr(module, "Plugin", None)

        if plugin_class is None:
            raise RuntimeError("Plugin must define class Plugin")

        instance = plugin_class()
        instance.file_path = str(path)

        if not isinstance(instance, PluginBase):
            raise RuntimeError("Plugin must inherit PluginBase")

        return instance

    def unload_all(self):
        for plugin in self.loaded_plugins:
            try:
                plugin.unload()
            except Exception as e:
                logger.error(f"Failed unloading {plugin.name()}: {e}")

        self.loaded_plugins.clear()

    def get_plugins_dir(self) -> Path:

        plugins = PLUGIN_DIR
        plugins.mkdir(parents=True, exist_ok=True)
        return plugins

