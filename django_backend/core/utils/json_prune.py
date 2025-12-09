# utils/json_prune.py
from __future__ import annotations

import json
import datetime as _dt
import decimal as _dec
import uuid as _uuid
from collections.abc import Mapping, Sequence, Set as AbcSet
from typing import Any, Tuple, List, Dict

# Sentinel for "dropped" values during pruning
_DROP = object()


def _to_jsonable_scalar(v: Any) -> Any:
    """
    Convert common non-JSON scalar types into JSONable representations.
    If the value is already JSON-serializable, return it as-is.
    If it cannot be serialized or converted, return _DROP.
    """
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        # ISO 8601 is a safe default for datetimes/dates/times
        return v.isoformat()
    if isinstance(v, (_dec.Decimal, _uuid.UUID)):
        return str(v)

    # Best-effort: attempt to json.dumps() unknown scalars
    try:
        json.dumps(v)
        return v
    except TypeError:
        return _DROP


def prune_non_jsonable(
    obj: Any,
    *,
    path: str = "",
    _visited: Dict[int, Any] | None = None,
    removed_paths: List[str] | None = None,
) -> Tuple[Any, List[str]]:
    """
    Recursively traverse an arbitrary Python object and remove or convert
    non-JSON-serializable parts. Returns (cleaned_obj, removed_paths).

    Behavior:
      - dict/Mapping: keep only JSONable items; keys are converted to str.
      - list/tuple/Sequence: keep only JSONable elements; output is a list.
      - set/AbcSet: converted to list; keep only JSONable elements.
      - other objects:
          * If convertible/JSONable scalar -> keep it.
          * Otherwise -> drop it (parent container records the path).

    Notes:
      - Paths use dot-notation for dict keys and [i] for sequence/set indices,
        e.g. "user.profile.avatars[2]".
      - Leaf nodes do NOT append to removed_paths themselves; only the parent
        container records a single entry for the dropped child, to avoid
        duplicates.
      - Cycles are handled via an object-id visited map.
    """
    if removed_paths is None:
        removed_paths = []
    if _visited is None:
        _visited = {}

    obj_id = id(obj)
    if obj_id in _visited:
        # Prevent infinite recursion on cyclic graphs
        return _visited[obj_id], removed_paths

    # First, try treating this as a scalar
    scalar = _to_jsonable_scalar(obj)
    if scalar is not _DROP:
        return scalar, removed_paths

    # Mapping (dict-like)
    if isinstance(obj, Mapping):
        out: Dict[str, Any] = {}
        _visited[obj_id] = out
        for k, v in obj.items():
            key_str = str(k)
            child_path = f"{path}.{key_str}" if path else key_str
            cleaned_v, removed_paths = prune_non_jsonable(
                v,
                path=child_path,
                _visited=_visited,
                removed_paths=removed_paths,
            )
            if cleaned_v is _DROP:
                # Record exactly once at the parent
                removed_paths.append(f"{child_path} ({type(v).__name__}) -> DROPPED")
            else:
                out[key_str] = cleaned_v
        return out, removed_paths

    # Sequence (except str/bytes) -> output list
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        out_list: List[Any] = []
        _visited[obj_id] = out_list
        for i, v in enumerate(obj):
            child_path = f"{path}[{i}]" if path else f"[{i}]"
            cleaned_v, removed_paths = prune_non_jsonable(
                v,
                path=child_path,
                _visited=_visited,
                removed_paths=removed_paths,
            )
            if cleaned_v is _DROP:
                removed_paths.append(f"{child_path} ({type(v).__name__}) -> DROPPED")
            else:
                out_list.append(cleaned_v)
        return out_list, removed_paths

    # Set-like -> iterate and output list in arbitrary order
    if isinstance(obj, AbcSet):
        out_list: List[Any] = []
        _visited[obj_id] = out_list
        for i, v in enumerate(obj):
            child_path = f"{path}[{i}]" if path else f"[{i}]"
            cleaned_v, removed_paths = prune_non_jsonable(
                v,
                path=child_path,
                _visited=_visited,
                removed_paths=removed_paths,
            )
            if cleaned_v is _DROP:
                removed_paths.append(f"{child_path} ({type(v).__name__}) -> DROPPED")
            else:
                out_list.append(cleaned_v)
        return out_list, removed_paths

    # Non-scalar, non-container -> unhandled object, drop it
    return _DROP, removed_paths
