#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from .propagation import diff_dict, filter_excluded_keys, apply_safe

EXCLUDED_DEFAULT = [".env", "auth", "credentials"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    p = argparse.ArgumentParser(prog="hermes-update-propagate",
                                description="Demo hermes update propagation CLI (SOUL-compliant, safe by default)")
    p.add_argument("--source-old", required=True, help="Path to old profile config JSON")
    p.add_argument("--source-new", required=True, help="Path to new profile config JSON")
    p.add_argument("--propagate", action="store_true", help="Enable propagation")
    p.add_argument("--propagate-dry-run", action="store_true", help="Dry-run: show what would be applied")
    p.add_argument("--propagate-scope", choices=["linked", "all", "same-owner"], default="linked")
    p.add_argument("--targets", nargs="*", help="Explicit target profile dirs to apply to (optional)")
    p.add_argument("--excluded-keys", nargs="*", default=EXCLUDED_DEFAULT)
    p.add_argument("--yes", action="store_true", help="Apply changes (dangerous) — implicit with --propagate and --targets")
    args = p.parse_args()

    old = load_json(args.source_old)
    new = load_json(args.source_new)
    changes = diff_dict(old, new)
    changes = filter_excluded_keys(changes, args.excluded_keys)

    print("Found changes:")
    print(json.dumps(changes, indent=2, ensure_ascii=False))

    if not args.propagate:
        print("Propagation not enabled; exiting.")
        return

    if not changes:
        print("No changes to propagate.")
        return

    # Determine targets
    targets = args.targets or []
    if not targets:
        print("No explicit targets provided; defaulting to dry-run summary only (no writes).")
        return

    summaries = []
    for t in targets:
        profile_dir = Path(t).expanduser()
        if args.propagate_dry_run:
            s = apply_safe(str(profile_dir), changes, origin="hermes-update-cli", dry_run=True)
        else:
            if not args.yes:
                print(f"Skipping apply to {profile_dir} (require --yes to actually write)")
                s = {"profile": str(profile_dir), "outcome": "skipped-no-yes"}
            else:
                s = apply_safe(str(profile_dir), changes, origin="hermes-update-cli", dry_run=False)
        summaries.append(s)

    print("Propagation summaries:")
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
