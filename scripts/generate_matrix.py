import json
from pathlib import Path

# === CONFIGURATION ===
board = "nice_nano_v2"
# automatically find all *.keymap filenames under ../config/keymap
keymap_dir = Path(__file__).parent.parent / "config" / "keymap"
keymaps = sorted(p.stem for p in keymap_dir.glob("*.keymap"))

groups = []
for keymap in keymaps:
    groups.append({
        "keymap": keymap,
        "format": "bt",
        "name": f"{keymap}-bt",
        "board": board,
    })

# single reset entry
groups.append({
    "keymap": "default",
    "format": "reset",
    "name": "reset-nanov2",
    "board": board,
})

# Dump matrix as compact JSON (GitHub expects it this way)
print(json.dumps(groups))
