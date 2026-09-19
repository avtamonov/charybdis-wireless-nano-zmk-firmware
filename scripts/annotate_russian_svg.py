"""Add Russian host-layout legends to Base keys in generated keymap-drawer SVGs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from keymap_legends import BASE_LATIN, BASE_RUSSIAN


def annotate(svg: str) -> str:
    layer_start = re.search(r'<g transform="[^"]+" class="layer-Base">', svg)
    if layer_start is None:
        raise ValueError("Base layer not found in SVG")
    next_layer = re.search(
        r'\n<g transform="[^"]+" class="layer-[^"]+">', svg[layer_start.end():]
    )
    end = layer_start.end() + next_layer.start() if next_layer else svg.rfind("</svg>")
    base = svg[layer_start.start():end]

    for position, (latin, russian) in enumerate(zip(BASE_LATIN, BASE_RUSSIAN, strict=True)):
        pattern = re.compile(
            rf'(<g transform="[^"]+" class="key[^"]* keypos-{position}">\s*'
            rf'<rect[^>]+/>)(.*?)(</g>)',
            re.DOTALL,
        )
        matches = list(pattern.finditer(base))
        if len(matches) != 1:
            raise ValueError(f"Expected one Base key at position {position}, got {len(matches)}")
        match = matches[0]
        if f'class="key tap">{latin}</text>' not in match.group(2):
            raise ValueError(f"Base position {position} no longer has tap {latin!r}")
        if 'data-russian-legend="true"' in match.group(2):
            continue
        addition = (
            '\n<text x="20" y="-18" class="key ru" '
            'data-russian-legend="true" '
            'style="font-size:10px;text-anchor:end;fill:#126CA0">'
            f'{russian}</text>'
        )
        base = base[:match.end(1)] + addition + base[match.end(1):]

    return svg[:layer_start.start()] + base + svg[end:]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svgs", type=Path, nargs="+")
    args = parser.parse_args()
    for path in args.svgs:
        original = path.read_text(encoding="utf-8")
        updated = annotate(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
