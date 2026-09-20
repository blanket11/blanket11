from __future__ import annotations

from pathlib import Path
import re

SOURCE = Path("profile-3d-contrib/profile-night-view.svg")
TARGET = Path("profile-3d-contrib/profile-night-view-clean.svg")

svg = SOURCE.read_text(encoding="utf-8")

# github-profile-3d-contrib writes the contribution bars as the first
# root-level <g>. Later root-level groups contain the radar chart,
# language pie and public-repository summary metrics.
tag_re = re.compile(r"</?g\b[^>]*>")
depth = 0
start = None
end = None

for match in tag_re.finditer(svg):
    tag = match.group(0)
    is_close = tag.startswith("</")

    if not is_close:
        if depth == 0 and start is None:
            start = match.start()
        depth += 1
    else:
        depth -= 1
        if depth == 0 and start is not None:
            end = match.end()
            break

if start is None or end is None:
    raise RuntimeError("Could not locate the 3D contribution group")

clean = svg[:start] + svg[start:end] + "</svg>"
TARGET.write_text(clean, encoding="utf-8")
