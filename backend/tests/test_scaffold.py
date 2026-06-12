import importlib
import inspect
from pathlib import Path

import pytest


def test_app_package_imports():
    module = importlib.import_module("app")
    assert module is not None


@pytest.mark.parametrize(
    "relative_path",
    [
        "api/v1/routers",
        "services",
        "repositories",
        "models",
        "schemas",
        "core",
        "integrations",
        "workers",
    ],
)
def test_layer_packages_exist(relative_path: str):
    package_root = Path(__file__).resolve().parents[1] / "app"
    init_file = package_root / relative_path / "__init__.py"
    assert init_file.is_file(), f"missing {init_file}"


@pytest.mark.parametrize(
    "module_path,reserved_for",
    [
        ("app.core.exceptions", "C-05"),
    ],
)
def test_core_slots_are_documented_placeholders(module_path: str, reserved_for: str):
    module = importlib.import_module(module_path)
    docstring = inspect.getdoc(module) or ""
    assert "RESERVADO" in docstring
    assert reserved_for in docstring

    public_names = [name for name in dir(module) if not name.startswith("_")]
    assert public_names == []


def test_dependencies_expose_auth_slots():
    from app.core import dependencies, permissions, tenancy

    deps_source = inspect.getsource(dependencies)
    assert "get_current_user" in deps_source
    assert "get_db" in deps_source
    perm_source = inspect.getsource(permissions)
    assert "require_permission" in perm_source
    assert "get_tenant" in inspect.getsource(tenancy)
