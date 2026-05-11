"""utils/standards.py — Runtime management of air quality standards.

Built-in standards live in config.py and are never modified on disk.
User-added standards and edits to built-in values are persisted in
dashboard/user_standards.json so they survive page reloads.

Schema of user_standards.json:
{
    "user_standards": {
        "<name>": {
            "pm2_5_target": float|null, "pm10_target": float|null, ...,
            "_meta": {"year": int, "source": str, "notes": str}  # optional
        }
    },
    "overrides": {
        "<builtin_name>": {"pm2_5_target": float, ...}   # only changed keys
    }
}
"""
import json
from pathlib import Path
from typing import Dict, Optional

from config import COMPOUND_STANDARDS

BUILTIN_NAMES = set(COMPOUND_STANDARDS.keys())  # {"WHO 2021", "EU 2024", "US EPA", "ECOWAS", "Custom"}

COMPOUND_KEYS = [
    "pm2_5_target", "pm10_target", "dust_target",
    "co_target", "no2_target", "o3_target", "so2_target", "aod_target",
]

_USER_FILE = Path(__file__).parent.parent / "user_standards.json"

_EMPTY: Dict = {"user_standards": {}, "overrides": {}}


# ── Persistence ────────────────────────────────────────────────────────────────

def _load_file() -> Dict:
    try:
        if _USER_FILE.exists():
            data = json.loads(_USER_FILE.read_text())
            data.setdefault("user_standards", {})
            data.setdefault("overrides", {})
            return data
    except Exception:
        pass
    return {"user_standards": {}, "overrides": {}}


def _save_file(data: Dict) -> None:
    _USER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Public API ─────────────────────────────────────────────────────────────────

def get_all_standards() -> Dict[str, Dict]:
    """Return merged dict of all standards: built-ins + user overrides + user additions."""
    data = _load_file()
    merged = {}
    for name, values in COMPOUND_STANDARDS.items():
        base = dict(values)
        if name in data["overrides"]:
            base.update({k: v for k, v in data["overrides"][name].items() if v is not None})
        merged[name] = base
    for name, values in data["user_standards"].items():
        merged[name] = {k: values.get(k) for k in COMPOUND_KEYS}
    return merged


def get_all_threshold_standards() -> Dict[str, Optional[float]]:
    """Return {name: pm2_5_target} for all standards — mirrors THRESHOLD_STANDARDS shape."""
    result = {}
    for name, vals in get_all_standards().items():
        result[name] = vals.get("pm2_5_target")
    return result


def is_builtin(name: str) -> bool:
    return name in BUILTIN_NAMES


def get_standard_meta(name: str) -> Dict:
    """Return metadata dict (year, source, notes) for a user standard."""
    if name in BUILTIN_NAMES:
        return {}
    data = _load_file()
    entry = data["user_standards"].get(name, {})
    return dict(entry.get("_meta", {}))


def add_standard(name: str, values: Dict, meta: Optional[Dict] = None) -> bool:
    """Add a new user standard. Returns False if name already exists."""
    data = _load_file()
    if name in BUILTIN_NAMES or name in data["user_standards"]:
        return False
    entry: Dict = {k: values.get(k) for k in COMPOUND_KEYS}
    if meta:
        entry["_meta"] = {k: v for k, v in meta.items() if v is not None}
    data["user_standards"][name] = entry
    _save_file(data)
    return True


def update_standard(name: str, values: Dict) -> None:
    """Update values for any standard (built-in via overrides, user standards directly)."""
    data = _load_file()
    if name in BUILTIN_NAMES:
        current = data["overrides"].setdefault(name, {})
        current.update({k: v for k, v in values.items() if k in COMPOUND_KEYS})
        data["overrides"][name] = current
    elif name in data["user_standards"]:
        current = data["user_standards"][name]
        current.update({k: v for k, v in values.items() if k in COMPOUND_KEYS})
        data["user_standards"][name] = current
    _save_file(data)


def delete_standard(name: str) -> bool:
    """Delete a user-added standard. Returns False if it's a built-in."""
    if name in BUILTIN_NAMES:
        return False
    data = _load_file()
    if name in data["user_standards"]:
        del data["user_standards"][name]
        _save_file(data)
        return True
    return False


def update_standard_meta(name: str, meta: Dict) -> None:
    """Update metadata (year, source, notes) for a user-added standard."""
    if name in BUILTIN_NAMES:
        return
    data = _load_file()
    if name not in data["user_standards"]:
        return
    cleaned = {k: v for k, v in meta.items() if v is not None}
    if cleaned:
        data["user_standards"][name]["_meta"] = cleaned
    else:
        data["user_standards"][name].pop("_meta", None)
    _save_file(data)


def reset_standard(name: str) -> None:
    """Reset a built-in standard's overrides back to config.py defaults."""
    if name not in BUILTIN_NAMES:
        return
    data = _load_file()
    data["overrides"].pop(name, None)
    _save_file(data)
