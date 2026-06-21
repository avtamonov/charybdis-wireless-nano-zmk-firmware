import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
BUILD_YAML = ROOT / "build.yaml"
KEYMAP_DIR = ROOT / "config" / "keymap"


def read_yaml_list(section):
    values = []
    in_section = False

    for raw_line in BUILD_YAML.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue

        if not raw_line.startswith((" ", "\t")) and line.endswith(":"):
            in_section = line[:-1] == section
            continue

        if in_section:
            stripped = line.strip()
            if stripped.startswith("- "):
                values.append(stripped[2:].strip().strip('"\''))
            elif not raw_line.startswith((" ", "\t")):
                break

    return values


def generate_matrix():
    boards = read_yaml_list("board") or ["nice_nano_v2/nrf52840"]
    keymaps = read_yaml_list("keymap") or sorted(p.stem for p in KEYMAP_DIR.glob("*.keymap"))
    formats = read_yaml_list("format") or ["bt", "reset"]

    keymaps = [keymap for keymap in keymaps if (KEYMAP_DIR / f"{keymap}.keymap").exists()]
    groups = []

    if "bt" in formats:
        for keymap in keymaps:
            groups.append({
                "keymap": keymap,
                "format": "bt",
                "name": f"{keymap}-bt",
                "board": boards[0],
            })

    if "reset" in formats:
        groups.append({
            "keymap": "default",
            "format": "reset",
            "name": "reset-nanov2",
            "board": boards[0],
        })

    return groups


if __name__ == "__main__":
    print(json.dumps(generate_matrix()))
