"""Function selection and scoring for pip-skill."""

from __future__ import annotations

import importlib
import inspect
import logging
from difflib import SequenceMatcher

from pip_skill.introspect import CallableInfo, PackageInfo

logger = logging.getLogger("pip_skill.selector")

VERB_PREFIXES = {
    "get",
    "set",
    "create",
    "delete",
    "update",
    "add",
    "remove",
    "find",
    "search",
    "list",
    "check",
    "is",
    "has",
    "make",
    "build",
    "parse",
    "read",
    "write",
    "load",
    "save",
    "send",
    "fetch",
    "put",
    "post",
    "patch",
    "open",
    "close",
    "start",
    "stop",
    "run",
    "execute",
    "process",
    "convert",
    "transform",
    "validate",
    "verify",
    "format",
    "encode",
    "decode",
    "connect",
    "disconnect",
    "init",
    "configure",
    "reset",
    "clear",
    "dump",
    "export",
    "import_",
    "request",
}


def score_module_depth(qualname: str, import_name: str) -> int:
    """Top-level module = 15, each submodule level = -3, min 0.

    Args:
        qualname: Fully qualified callable name (e.g., 'requests.api.get').
        import_name: Top-level import name (e.g., 'requests').

    Returns:
        Score from 0 to 15.
    """
    module_part = qualname.rsplit(".", 1)[0]
    depth = module_part.count(".") - import_name.count(".")
    return max(0, 15 - (depth * 3))


def score_all_membership(name: str, top_module) -> int:
    """Check if name is in the top-level module's __all__.

    Args:
        name: Function name.
        top_module: The top-level imported module.

    Returns:
        12 if in __all__, 0 otherwise.
    """
    if hasattr(top_module, "__all__") and name in top_module.__all__:
        return 12
    return 0


def score_docstring(fn) -> int:
    """Score based on docstring quality.

    Args:
        fn: The callable object.

    Returns:
        Score from 0 to 15.
    """
    from docstring_parser import parse as parse_docstring

    doc = inspect.getdoc(fn)
    if not doc:
        return 0
    score = 5  # has docstring
    parsed = parse_docstring(doc)
    if parsed.params:
        score += 5  # has parameter docs
    if parsed.examples or ">>>" in doc or "example" in doc.lower():
        score += 5  # has examples
    return score


def score_annotations(callable_info: CallableInfo) -> int:
    """Percentage of params with annotations, scaled 0-10.

    Args:
        callable_info: The callable to score.

    Returns:
        Score from 0 to 10.
    """
    params = [p for p in callable_info.parameters if p.name != "self"]
    if not params:
        return 10  # no params = fully "annotated"
    annotated = sum(1 for p in params if p.annotation)
    return round((annotated / len(params)) * 10)


def score_name(name: str) -> int:
    """Score based on name quality (verb prefix, length, no underscore prefix).

    Args:
        name: The callable name.

    Returns:
        Score from 0 to 10.
    """
    score = 0
    if not name.startswith("_"):
        score += 3
    parts = name.split("_")
    if parts[0].lower() in VERB_PREFIXES:
        score += 4
    if len(name) <= 30:
        score += 3
    return score


def score_param_count(callable_info: CallableInfo) -> int:
    """Sweet spot is 1-5 parameters.

    Args:
        callable_info: The callable to score.

    Returns:
        Score from 0 to 8.
    """
    n = len([p for p in callable_info.parameters if p.name != "self"])
    if 1 <= n <= 5:
        return 8
    if 6 <= n <= 10:
        return 5
    if n == 0:
        return 3
    return 1  # 11+


def score_not_deprecated(fn) -> int:
    """Check if function is not deprecated.

    Args:
        fn: The callable object.

    Returns:
        5 if not deprecated, 0 if deprecated.
    """
    doc = inspect.getdoc(fn) or ""
    if "deprecated" in doc.lower() or "obsolete" in doc.lower():
        return 0
    return 5


def score_uniqueness(callable_info: CallableInfo, higher_scored: list[CallableInfo]) -> int:
    """Penalize near-duplicates of already-selected functions.

    Args:
        callable_info: The callable to score.
        higher_scored: Previously selected callables (higher-scored).

    Returns:
        Score from 0 to 10.
    """
    name = callable_info.name.lower().replace("_", "")
    # Check name similarity first across all candidates
    for other in higher_scored:
        other_name = other.name.lower().replace("_", "")
        ratio = SequenceMatcher(None, name, other_name).ratio()
        if ratio > 0.8:
            return 0  # very similar name — deduplicate
    # Then check param similarity
    my_params = {p.name for p in callable_info.parameters if p.name != "self"}
    for other in higher_scored:
        other_params = {p.name for p in other.parameters if p.name != "self"}
        if my_params and my_params == other_params:
            return 2  # same params, probably a variant
    return 10


def score_reexport(name: str, fn, top_module) -> int:
    """Check if function is accessible from top-level package.

    Args:
        name: Function name.
        fn: The callable object.
        top_module: The top-level imported module.

    Returns:
        10 if accessible at top level, 0 otherwise.
    """
    try:
        top_obj = getattr(top_module, name, None)
        if top_obj is fn:
            return 10
    except Exception:
        pass
    return 0


def _resolve_callable(callable_info: CallableInfo):
    """Attempt to resolve a CallableInfo back to a live Python object.

    Args:
        callable_info: The callable to resolve.

    Returns:
        The callable object, or None if it cannot be resolved.
    """
    try:
        mod = importlib.import_module(callable_info.module)
        obj = getattr(mod, callable_info.name, None)
        if obj is not None and callable(obj):
            return obj
    except Exception:
        pass
    return None


def select_functions(
    package_info: PackageInfo,
    max_tools: int = 20,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    threshold: int = 40,
    verbose: bool = False,
) -> list[tuple[CallableInfo, int]]:
    """Select and rank functions for wrapping.

    Args:
        package_info: The introspected package.
        max_tools: Maximum number of functions to return.
        include_patterns: Optional glob patterns to include (e.g., ['get*']).
        exclude_patterns: Optional glob patterns to exclude.
        threshold: Minimum score to include (default 40, lowered to 20 if no results).
        verbose: If True, print scoring breakdown.

    Returns:
        List of (callable_info, score) tuples sorted by score descending.
    """
    import fnmatch

    try:
        top_module = importlib.import_module(package_info.import_name)
    except ImportError:
        top_module = None

    logger.info("Selecting functions from %s (max %d)", package_info.name, max_tools)

    # Collect all candidates from all modules (functions + class constructors)
    candidates: list[CallableInfo] = []
    for mod in package_info.modules:
        for fn_info in mod.callables:
            if include_patterns and not any(
                fnmatch.fnmatch(fn_info.name, p) for p in include_patterns
            ):
                continue
            if exclude_patterns and any(fnmatch.fnmatch(fn_info.name, p) for p in exclude_patterns):
                continue
            candidates.append(fn_info)

        # Include class constructors as candidates
        for cls_info in mod.classes:
            if cls_info.name.startswith("_"):
                continue
            if include_patterns and not any(
                fnmatch.fnmatch(cls_info.name, p) for p in include_patterns
            ):
                continue
            if exclude_patterns and any(
                fnmatch.fnmatch(cls_info.name, p) for p in exclude_patterns
            ):
                continue
            # Convert class __init__ to a CallableInfo pseudo-entry
            init_params = [p for p in cls_info.init_params if p.name != "self"]
            param_strs = []
            for p in init_params:
                s = p.name
                if p.annotation:
                    s += f": {p.annotation}"
                if p.has_default and p.default is not None:
                    s += f" = {p.default}"
                param_strs.append(s)
            sig = f"({', '.join(param_strs)})"
            cls_callable = CallableInfo(
                name=cls_info.name,
                qualname=f"{mod.name}.{cls_info.name}",
                module=mod.name,
                signature=sig,
                parameters=init_params,
                return_type=cls_info.name,
                docstring=cls_info.docstring,
                is_async=False,
                is_method=False,
                is_classmethod=False,
                is_staticmethod=False,
                is_property=False,
                has_varargs=any(p.kind == "var_positional" for p in init_params),
                has_varkw=any(p.kind == "var_keyword" for p in init_params),
                decorators=[],
                source_available=False,
            )
            candidates.append(cls_callable)

            # Surface the class's instance methods so the canonical
            # `requests.Session().get()` and `boto3.client('s3').list_buckets()`
            # patterns are scored alongside top-level functions.
            for method in cls_info.methods:
                if method.name.startswith("_"):
                    continue
                if include_patterns and not any(
                    fnmatch.fnmatch(method.name, p) for p in include_patterns
                ):
                    continue
                if exclude_patterns and any(
                    fnmatch.fnmatch(method.name, p) for p in exclude_patterns
                ):
                    continue
                # Construct a method-flavoured CallableInfo. Skip params named `self`.
                method_params = [p for p in method.parameters if p.name != "self"]
                method_callable = CallableInfo(
                    name=method.name,
                    qualname=f"{mod.name}.{cls_info.name}.{method.name}",
                    module=mod.name,
                    signature=method.signature,
                    parameters=method_params,
                    return_type=method.return_type,
                    docstring=method.docstring,
                    is_async=method.is_async,
                    is_method=True,
                    is_classmethod=method.is_classmethod,
                    is_staticmethod=method.is_staticmethod,
                    is_property=method.is_property,
                    has_varargs=method.has_varargs,
                    has_varkw=method.has_varkw,
                    decorators=method.decorators,
                    source_available=method.source_available,
                )
                candidates.append(method_callable)

    # Score each candidate (except uniqueness, which needs ordering)
    scored: list[tuple[CallableInfo, int]] = []
    for fn_info in candidates:
        fn_obj = _resolve_callable(fn_info)

        depth_score = score_module_depth(fn_info.qualname, package_info.import_name)
        all_score = score_all_membership(fn_info.name, top_module) if top_module else 0
        doc_score = score_docstring(fn_obj) if fn_obj else 0
        ann_score = score_annotations(fn_info)
        name_score = score_name(fn_info.name)
        param_score = score_param_count(fn_info)
        return_score = 5 if fn_info.return_type else 0
        dep_score = score_not_deprecated(fn_obj) if fn_obj else 5
        reexport_score = (
            score_reexport(fn_info.name, fn_obj, top_module) if (fn_obj and top_module) else 0
        )

        base_score = (
            depth_score
            + all_score
            + doc_score
            + ann_score
            + name_score
            + param_score
            + return_score
            + dep_score
            + reexport_score
        )

        if verbose:
            import sys

            print(f"Scoring: {fn_info.qualname}", file=sys.stderr)
            print(f"  module_depth:    {depth_score:2d}", file=sys.stderr)
            print(f"  all_membership:  {all_score:2d}", file=sys.stderr)
            print(f"  docstring:       {doc_score:2d}", file=sys.stderr)
            print(f"  annotations:     {ann_score:2d}", file=sys.stderr)
            print(f"  name_quality:    {name_score:2d}", file=sys.stderr)
            print(f"  param_count:     {param_score:2d}", file=sys.stderr)
            print(f"  return_type:     {return_score:2d}", file=sys.stderr)
            print(f"  not_deprecated:  {dep_score:2d}", file=sys.stderr)
            print(f"  reexport:        {reexport_score:2d}", file=sys.stderr)
            print(f"  BASE:            {base_score}", file=sys.stderr)

        scored.append((fn_info, base_score))

    # Sort by base score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    def _apply_uniqueness(
        sorted_scored: list[tuple[CallableInfo, int]],
        min_threshold: int,
    ) -> list[tuple[CallableInfo, int]]:
        final = []
        selected: list[CallableInfo] = []
        for fn_info, base_score in sorted_scored:
            uniqueness = score_uniqueness(fn_info, selected)
            total = base_score + uniqueness
            if verbose:
                import sys

                print(f"  uniqueness:      {uniqueness:2d}  -> TOTAL: {total}", file=sys.stderr)
            # uniqueness == 0 means very similar name to already-selected function — skip
            if uniqueness == 0 and selected:
                continue
            if total >= min_threshold:
                final.append((fn_info, total))
                selected.append(fn_info)
        return final

    final = _apply_uniqueness(scored, threshold)

    # If nothing passes threshold, lower to 20
    if not final and scored:
        import warnings

        warnings.warn(
            f"No functions scored above {threshold}. Lowering threshold to 20.",
            stacklevel=2,
        )
        final = _apply_uniqueness(scored, 20)

    return final[:max_tools]


def llm_curate(
    candidates: list[tuple[CallableInfo, int]],
    package_info: PackageInfo,
    max_tools: int,
    api_key: str,
    deterministic: bool = False,
) -> list[CallableInfo]:
    """Use Claude to curate function selection.

    Args:
        candidates: Heuristic-scored candidates (top 30 used).
        package_info: Package metadata.
        max_tools: Max tools to return.
        api_key: Anthropic API key.
        deterministic: When True, force `temperature=0` so the same
            input produces the same ranking across runs (still subject
            to provider-side model drift).

    Returns:
        List of selected CallableInfo objects in LLM-ranked order.
    """
    import json

    import anthropic

    top = candidates[:30]
    lines = []
    for rank, (fn_info, score) in enumerate(top, 1):
        doc = fn_info.docstring or ""
        first_para = doc.split("\n\n")[0].replace("\n", " ").strip()[:200]
        param_count = len(fn_info.parameters)
        annotated = sum(1 for p in fn_info.parameters if p.annotation)
        lines.append(
            f"## {rank}. {fn_info.qualname} (score: {score})\n"
            f"Signature: {fn_info.signature}\n"
            f"Docstring: {first_para}\n"
            f"Module: {fn_info.module}\n"
            f"Params: {param_count} ({annotated} annotated)\n"
        )
    candidate_list = "\n".join(lines)

    prompt = (
        f"You are selecting the most useful functions from a Python package to expose as AI assistant tools.\n\n"
        f"Package: {package_info.name} v{package_info.version}\n"
        f"Description: {package_info.description}\n\n"
        f"Below are the top {len(top)} candidate functions, ranked by automated scoring.\n"
        f"For each function, I've included its signature, docstring summary, and score.\n\n"
        f"{candidate_list}\n"
        f"Select the {max_tools} most useful functions for an AI assistant. Prioritize:\n"
        f"1. Functions that perform complete, useful operations (not internal helpers)\n"
        f"2. Functions with clear inputs and outputs\n"
        f"3. Functions that cover the package's primary use cases\n"
        f"4. Diversity of functionality (don't select 5 variants of the same operation)\n\n"
        f'Respond with a JSON array of function names in priority order:\n["function_name_1", "function_name_2", ...]'
    )

    client = anthropic.Anthropic(api_key=api_key)
    # Model is overridable via env so users can opt into newer models without
    # waiting for a release. Default tracks the latest GA Sonnet at the time
    # of the last release.
    import os

    model = os.environ.get("PIP_SKILL_MODEL", "claude-sonnet-4-5")
    create_kwargs = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if deterministic:
        create_kwargs["temperature"] = 0
    response = client.messages.create(**create_kwargs)

    text = response.content[0].text
    # Extract JSON array from response
    try:
        start = text.index("[")
        end = text.rindex("]") + 1
        selected_names = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        # Fallback: return heuristic top
        return [fn for fn, _ in candidates[:max_tools]]

    name_to_info = {fn.name: fn for fn, _ in candidates}
    result = [name_to_info[name] for name in selected_names if name in name_to_info]
    return result[:max_tools]
