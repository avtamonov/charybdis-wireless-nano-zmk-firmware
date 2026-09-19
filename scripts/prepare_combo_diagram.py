"""Prepare a print-only keymap for Keymap Drawer's combo renderer.

Only metadata changes here; Keymap Drawer draws every key, combo box and arc.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


EXCLUDED_ACTIONS = {
    ("Caret", "toggle"),
    ("Reset", "toggle"),
    ("Base", "toggle"),
    ("Function", "sticky"),
    ("Game", "toggle"),
    ("BOOT LDR", ""),
    ("ZMK Studio", ""),
}
PRINT_LABELS = {
    "Double Shift": "2×Shift",
    "ESCAPE": "Esc",
    "TAB": "Tab",
    "Ctl+ BACK SPACE": "Ctrl+Bksp",
    "Gui+ SPACE": "Win+Space",
}


def tap_and_hold(key: object) -> tuple[str, str]:
    if isinstance(key, dict):
        return str(key.get("t", "")), str(key.get("h", ""))
    return str(key), ""


def prepare(source: Path, output: Path) -> None:
    with source.open(encoding="utf-8") as stream:
        keymap = yaml.safe_load(stream)

    combos = []
    used_positions = set()
    for combo in keymap["combos"]:
        action, hold = tap_and_hold(combo["k"])
        if (action, hold) in EXCLUDED_ACTIONS:
            continue
        if len(combo["p"]) != 2:
            raise ValueError(f"Expected a two-key combo: {combo!r}")
        used_positions.update(combo["p"])
        combos.append({
            "p": combo["p"],
            "k": PRINT_LABELS.get(action, action),
            "l": ["Combos"],
            "w": 55 if action in {"Ctl+ BACK SPACE", "Gui+ SPACE"} else 44,
        })
    if not combos:
        raise ValueError("No printable combos found")

    base = keymap["layers"]["Base"]
    keys = [tap_and_hold(key)[0] if index in used_positions else ""
            for index, key in enumerate(base)]
    drawing = {
        "layout": keymap["layout"],
        "layers": {"Combos": keys},
        "combos": combos,
        "draw_config": {
            "separate_combo_diagrams": False,
            "dark_mode": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(drawing, stream, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keymap", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.keymap, args.output)
