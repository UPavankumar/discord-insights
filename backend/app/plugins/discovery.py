from __future__ import annotations

import importlib
import inspect
import pkgutil

from app.plugins.base import Plugin
from app.plugins.registry import PluginRegistry


def discover_plugins(
    package_name: str = "app.plugins",
) -> PluginRegistry:
    """
    Discover and instantiate every concrete Plugin subclass
    inside the plugin package.

    Adding a plugin means adding a Python file.
    No registry modification is required.
    """

    registry = PluginRegistry()

    package = importlib.import_module(package_name)

    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = module_info.name

        if module_name.startswith("_"):
            continue

        if module_name in {"base", "registry", "discovery"}:
            continue

        module = importlib.import_module(
            f"{package_name}.{module_name}"
        )

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Plugin)
                and obj is not Plugin
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                registry.register(obj())

    return registry
