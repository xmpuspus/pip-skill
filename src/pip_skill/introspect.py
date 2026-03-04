"""Package introspection engine for pip-skill."""

from __future__ import annotations

import contextlib
import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from typing import get_type_hints


@dataclass
class ParamInfo:
    """Information about a single function parameter."""

    name: str
    annotation: str | None
    default: str | None
    has_default: bool
    kind: str  # "positional", "keyword", "positional_or_keyword", "var_positional", "var_keyword"


@dataclass
class CallableInfo:
    """Information about a callable (function, method, builtin)."""

    name: str
    qualname: str
    module: str
    signature: str
    parameters: list[ParamInfo]
    return_type: str | None
    docstring: str | None
    is_async: bool
    is_method: bool
    is_classmethod: bool
    is_staticmethod: bool
    is_property: bool
    has_varargs: bool
    has_varkw: bool
    decorators: list[str]
    source_available: bool


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    qualname: str
    module: str
    bases: list[str]
    docstring: str | None
    methods: list[CallableInfo]
    is_pydantic_model: bool
    init_params: list[ParamInfo]


@dataclass
class ModuleInfo:
    """Information about a single module."""

    name: str
    is_package: bool
    callables: list[CallableInfo]
    classes: list[ClassInfo]
    has_all: bool
    all_names: list[str] | None


@dataclass
class PackageInfo:
    """Complete information about an introspected package."""

    name: str
    import_name: str
    version: str
    description: str
    author: str | None
    homepage: str | None
    license: str | None
    dependencies: list[str]
    modules: list[ModuleInfo]
    tier: int
    annotation_coverage: float


def _format_type(annotation) -> str:
    """Format a type annotation as a human-readable string."""
    if annotation is None:
        return "None"
    if annotation is inspect.Parameter.empty:
        return ""
    if isinstance(annotation, str):
        return annotation
    if hasattr(annotation, "__name__"):
        return annotation.__name__
    return str(annotation).replace("typing.", "")


def resolve_import_name(pip_name: str) -> str:
    """Find the import name for a pip package.

    Args:
        pip_name: The pip package name (e.g., 'Pillow', 'python-dateutil').

    Returns:
        The Python import name (e.g., 'PIL', 'dateutil').

    Raises:
        ValueError: If the import name cannot be resolved.
    """
    from importlib.metadata import packages_distributions

    mapping = packages_distributions()

    # Search mapping: import_name -> [pip_names]
    for import_name, pip_names in mapping.items():
        if pip_name in pip_names or pip_name.lower() in [p.lower() for p in pip_names]:
            return import_name

    # Fallback: try common transformations
    candidates = [
        pip_name,
        pip_name.replace("-", "_"),
        pip_name.lower(),
        pip_name.lower().replace("-", "_"),
    ]
    for candidate in candidates:
        try:
            importlib.import_module(candidate)
            return candidate
        except ImportError:
            continue

    raise ValueError(f"Package '{pip_name}' is not installed. Run: pip install {pip_name}")


def get_package_metadata(pip_name: str) -> dict:
    """Read package metadata from importlib.metadata.

    Args:
        pip_name: The pip package name.

    Returns:
        Dict with name, version, summary, author, homepage, license.
    """
    from importlib.metadata import metadata

    m = metadata(pip_name)
    homepage = m["Home-page"] or ""
    # Prefer Project-URL: Homepage if available
    project_urls = m.get_all("Project-URL") or []
    for url_entry in project_urls:
        if url_entry and "homepage" in url_entry.lower():
            parts = url_entry.split(", ", 1)
            if len(parts) == 2:
                homepage = parts[1].strip()
                break

    return {
        "name": m["Name"] or pip_name,
        "version": m["Version"] or "unknown",
        "summary": m["Summary"] or "",
        "author": m["Author"] or m.get("Author-email") or "",
        "homepage": homepage,
        "license": m["License"] or "",
    }


def get_required_dependencies(pip_name: str) -> list[str]:
    """Get required dependencies, excluding extras and platform-conditional deps.

    Args:
        pip_name: The pip package name.

    Returns:
        List of required dependency names.
    """
    from importlib.metadata import requires

    raw = requires(pip_name) or []
    required = []
    for dep in raw:
        if "; extra ==" in dep:
            continue
        dep_name = dep.split(";")[0].strip()
        dep_name = dep_name.split("[")[0]
        dep_name = dep_name.split("<")[0].split(">")[0].split("=")[0].split("!")[0]
        dep_name = dep_name.strip()
        if dep_name:
            required.append(dep_name)
    return required


def walk_package_modules(
    import_name: str,
) -> list[tuple[str, object | None, str | None]]:
    """Walk all submodules of a package.

    Args:
        import_name: The Python import name.

    Returns:
        List of (module_name, module_or_None, error_or_None) tuples.
    """
    results = []
    try:
        pkg = importlib.import_module(import_name)
    except Exception as e:
        return [(import_name, None, str(e))]

    results.append((import_name, pkg, None))

    if not hasattr(pkg, "__path__"):
        return results

    for modinfo in pkgutil.walk_packages(
        path=pkg.__path__,
        prefix=pkg.__name__ + ".",
        onerror=lambda name: None,
    ):
        try:
            mod = importlib.import_module(modinfo.name)
            results.append((modinfo.name, mod, None))
        except Exception as e:
            results.append((modinfo.name, None, str(e)))

    return results


def get_public_api(module) -> tuple[list, list, bool]:
    """Get public functions and classes from a module.

    Args:
        module: An imported Python module.

    Returns:
        Tuple of (functions, classes, has_all) where functions and classes are
        lists of (name, obj) pairs, and has_all indicates if __all__ was defined.
    """
    functions = []
    classes = []

    if hasattr(module, "__all__"):
        public_names = set(module.__all__)
        has_all = True
    else:
        public_names = set()
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name, None)
            if obj is None:
                continue
            obj_module = getattr(obj, "__module__", None)
            if obj_module and (
                obj_module == module.__name__ or obj_module.startswith(module.__name__ + ".")
            ):
                public_names.add(name)
        has_all = False

    for name in sorted(public_names):
        obj = getattr(module, name, None)
        if obj is None:
            continue
        try:
            if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                functions.append((name, obj))
            elif inspect.isclass(obj):
                classes.append((name, obj))
        except Exception:
            continue

    return functions, classes, has_all


def extract_callable_info(name: str, fn, module_name: str) -> CallableInfo:
    """Extract full information about a callable.

    Args:
        name: The callable's name.
        fn: The callable object.
        module_name: The module where it was found.

    Returns:
        CallableInfo with all extracted metadata.
    """
    # Get signature
    sig = None
    try:
        sig = inspect.signature(fn, eval_str=True)
    except (ValueError, TypeError):
        with contextlib.suppress(ValueError, TypeError):
            sig = inspect.signature(fn)

    # Get type hints
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    # Extract parameters
    parameters = []
    has_varargs = False
    has_varkw = False

    if sig:
        kind_map = {
            inspect.Parameter.POSITIONAL_ONLY: "positional",
            inspect.Parameter.POSITIONAL_OR_KEYWORD: "positional_or_keyword",
            inspect.Parameter.KEYWORD_ONLY: "keyword",
        }
        for pname, param in sig.parameters.items():
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                has_varargs = True
                continue
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                has_varkw = True
                continue

            annotation = None
            if pname in hints:
                annotation = _format_type(hints[pname])
            elif param.annotation is not inspect.Parameter.empty:
                annotation = _format_type(param.annotation)

            has_default = param.default is not inspect.Parameter.empty
            default = repr(param.default) if has_default else None

            parameters.append(
                ParamInfo(
                    name=pname,
                    annotation=annotation,
                    default=default,
                    has_default=has_default,
                    kind=kind_map.get(param.kind, "positional_or_keyword"),
                )
            )

    # Return type
    return_type = None
    if "return" in hints:
        return_type = _format_type(hints["return"])
    elif sig and sig.return_annotation is not inspect.Parameter.empty:
        return_type = _format_type(sig.return_annotation)

    # Docstring
    docstring = inspect.getdoc(fn)

    # Source availability
    source_available = True
    try:
        inspect.getsource(fn)
    except (OSError, TypeError):
        source_available = False

    is_async = inspect.iscoroutinefunction(fn)

    return CallableInfo(
        name=name,
        qualname=f"{module_name}.{name}",
        module=module_name,
        signature=str(sig) if sig else "(unknown)",
        parameters=parameters,
        return_type=return_type,
        docstring=docstring,
        is_async=is_async,
        is_method=False,
        is_classmethod=False,
        is_staticmethod=False,
        is_property=False,
        has_varargs=has_varargs,
        has_varkw=has_varkw,
        decorators=[],
        source_available=source_available,
    )


def extract_class_info(name: str, cls, module_name: str) -> ClassInfo:
    """Extract information about a class.

    Args:
        name: The class name.
        cls: The class object.
        module_name: The module where it was found.

    Returns:
        ClassInfo with all extracted metadata.
    """
    # Base classes
    bases = []
    for base in cls.__mro__[1:]:
        if base is object:
            continue
        bases.append(f"{base.__module__}.{base.__qualname__}")

    # Public methods
    methods = []
    for method_name, method_obj in inspect.getmembers(cls):
        if method_name.startswith("_") and method_name != "__init__":
            continue
        if not (inspect.isfunction(method_obj) or inspect.ismethod(method_obj)):
            continue
        if method_name in ("__repr__", "__str__", "__eq__", "__hash__"):
            continue
        try:
            info = extract_callable_info(method_name, method_obj, f"{module_name}.{name}")
            info.is_method = True
            methods.append(info)
        except Exception:
            continue

    # Detect Pydantic model
    is_pydantic = False
    try:
        from pydantic import BaseModel

        is_pydantic = issubclass(cls, BaseModel)
    except ImportError:
        pass

    # Init params
    init_params = []

    if is_pydantic and hasattr(cls, "model_fields"):
        for field_name, field_info in cls.model_fields.items():
            ann = _format_type(field_info.annotation) if field_info.annotation else None
            default = None
            if not field_info.is_required() and field_info.default is not None:
                try:
                    default = repr(field_info.default)
                except Exception:
                    default = None
            init_params.append(
                ParamInfo(
                    name=field_name,
                    annotation=ann,
                    default=default,
                    has_default=not field_info.is_required(),
                    kind="keyword",
                )
            )
    else:
        if hasattr(cls, "__init__"):
            try:
                sig = inspect.signature(cls.__init__, eval_str=True)
                for pname, param in sig.parameters.items():
                    if pname == "self":
                        continue
                    ann = None
                    if param.annotation is not inspect.Parameter.empty:
                        ann = _format_type(param.annotation)
                    has_default = param.default is not inspect.Parameter.empty
                    init_params.append(
                        ParamInfo(
                            name=pname,
                            annotation=ann,
                            default=repr(param.default) if has_default else None,
                            has_default=has_default,
                            kind="positional_or_keyword",
                        )
                    )
            except (ValueError, TypeError):
                pass

    return ClassInfo(
        name=name,
        qualname=f"{module_name}.{name}",
        module=module_name,
        bases=[b.split(".")[-1] for b in bases[:3]],
        docstring=inspect.getdoc(cls),
        methods=methods,
        is_pydantic_model=is_pydantic,
        init_params=init_params,
    )


def detect_tier(modules: list[ModuleInfo]) -> tuple[int, float]:
    """Auto-detect package tier and annotation coverage.

    Args:
        modules: List of introspected ModuleInfo objects.

    Returns:
        Tuple of (tier, annotation_coverage).
    """
    total_params = 0
    annotated_params = 0
    has_stateful_classes = False
    has_lazy_imports = False

    for mod_info in modules:
        for fn in mod_info.callables:
            for param in fn.parameters:
                total_params += 1
                if param.annotation:
                    annotated_params += 1

        for cls in mod_info.classes:
            non_init_methods = [m for m in cls.methods if m.name != "__init__"]
            if len(non_init_methods) > 3:
                has_stateful_classes = True

    coverage = annotated_params / total_params if total_params > 0 else 0.0

    if has_lazy_imports or has_stateful_classes and coverage < 0.5:
        tier = 3
    elif coverage >= 0.7:
        tier = 1
    else:
        tier = 2

    return tier, coverage


def introspect_package(pip_name: str) -> PackageInfo:
    """Introspect an installed pip package.

    Args:
        pip_name: The pip package name (e.g., 'requests', 'Pillow').

    Returns:
        PackageInfo with complete API information.

    Raises:
        ValueError: If the package is not installed or cannot be imported.
    """
    # Step 1: Resolve import name
    import_name = resolve_import_name(pip_name)

    # Step 2: Read metadata
    try:
        meta = get_package_metadata(pip_name)
    except Exception:
        # Package not installed via pip (e.g., local dev package on sys.path)
        meta = {
            "name": pip_name,
            "version": "unknown",
            "summary": "",
            "author": "",
            "homepage": "",
            "license": "",
        }

    # Step 3: Get dependencies
    try:
        deps = get_required_dependencies(pip_name)
    except Exception:
        deps = []

    # Step 4-6: Walk modules and enumerate API
    modules_data = walk_package_modules(import_name)
    modules = []

    for mod_name, mod, error in modules_data:
        if error or mod is None:
            continue
        try:
            functions, classes, has_all = get_public_api(mod)
        except Exception:
            continue

        callables = []
        for fn_name, fn_obj in functions:
            try:
                callables.append(extract_callable_info(fn_name, fn_obj, mod_name))
            except Exception:
                continue

        class_infos = []
        for cls_name, cls_obj in classes:
            try:
                class_infos.append(extract_class_info(cls_name, cls_obj, mod_name))
            except Exception:
                continue

        modules.append(
            ModuleInfo(
                name=mod_name,
                is_package=hasattr(mod, "__path__"),
                callables=callables,
                classes=class_infos,
                has_all=has_all,
                all_names=list(mod.__all__) if hasattr(mod, "__all__") else None,
            )
        )

    # Step 7: Detect tier
    tier, coverage = detect_tier(modules)

    return PackageInfo(
        name=meta["name"],
        import_name=import_name,
        version=meta["version"],
        description=meta["summary"],
        author=meta["author"] or None,
        homepage=meta["homepage"] or None,
        license=meta["license"] or None,
        dependencies=deps,
        modules=modules,
        tier=tier,
        annotation_coverage=coverage,
    )
