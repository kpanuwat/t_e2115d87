import json
import os
import tempfile
import time
from typing import Any, Dict, List


def diff_dict(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict of keys that changed or are new in `new` compared to `old`.
    Only shallow and nested dicts are handled recursively.
    """
    changes = {}
    for k, v in new.items():
        if k not in old:
            changes[k] = v
        else:
            if isinstance(v, dict) and isinstance(old.get(k), dict):
                nested = diff_dict(old[k], v)
                if nested:
                    changes[k] = nested
            else:
                if v != old.get(k):
                    changes[k] = v
    return changes


def _key_matches_excluded(key_path: str, excluded_patterns: List[str]) -> bool:
    # simple prefix or exact match
    for p in excluded_patterns:
        if key_path == p or key_path.startswith(p + "."):
            return True
    return False


def filter_excluded_keys(changes: Dict[str, Any], excluded_patterns: List[str], prefix: str = "") -> Dict[str, Any]:
    """Remove keys from changes that match any excluded pattern.
    Works recursively, preserving structure for nested dicts.
    prefix is used to build dotted key path during recursion.
    """
    out = {}
    for k, v in changes.items():
        kp = f"{prefix}.{k}" if prefix else k
        if _key_matches_excluded(kp, excluded_patterns):
            continue
        if isinstance(v, dict):
            nested = filter_excluded_keys(v, excluded_patterns, kp)
            if nested:
                out[k] = nested
        else:
            out[k] = v
    return out


def apply_safe(profile_dir: str, changes: Dict[str, Any], origin: str = "local", dry_run: bool = False) -> Dict[str, Any]:
    """Apply changes atomically to a JSON config file under profile_dir.
    Writes to config.json and appends a propagation.log entry. Returns a summary dict.
    If dry_run True, nothing is written and summary contains would_apply.
    """
    cfg_path = os.path.join(profile_dir, "config.json")
    log_path = os.path.join(profile_dir, "propagation.log")

    old = {}
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            try:
                old = json.load(f)
            except Exception:
                old = {}

    # shallow merge for simplicity (replace leaf values / nested dicts)
    new = dict(old)

    def merge(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                merge(dst[k], v)
            else:
                dst[k] = v

    merge(new, changes)

    summary = {
        "profile": profile_dir,
        "origin": origin,
        "keys_changed": list(changes.keys()),
        "timestamp": int(time.time()),
    }

    if dry_run:
        summary["would_apply"] = new
        summary["outcome"] = "dry-run"
        return summary

    # write atomically
    os.makedirs(profile_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="cfg-", dir=profile_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(new, f, indent=2, ensure_ascii=False)
        # atomic replace
        os.replace(tmp, cfg_path)
        outcome = "applied"
    except Exception as e:
        # cleanup tmp
        try:
            os.unlink(tmp)
        except Exception:
            pass
        outcome = f"error: {e}"

    # append log
    summary["outcome"] = outcome
    try:
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(json.dumps(summary, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return summary


if __name__ == "__main__":
    import sys
    print("propagation module: helper functions")
    sys.exit(0)
