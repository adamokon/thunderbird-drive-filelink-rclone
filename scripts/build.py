#!/usr/bin/env python3
"""Reproducible XPI: only explicitly scoped extension assets."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent.parent
version = json.loads((root / "extension/manifest.json").read_text())["version"]
output = root / "dist" / f"drive-filelink-rclone-{version}.xpi"
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root / "extension").iterdir()):
        if path.suffix not in (".json", ".js", ".html", ".css", ".svg"):
            raise SystemExit(f"Unexpected extension file: {path.name}")
        info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, path.read_bytes())
digest = hashlib.sha256(output.read_bytes()).hexdigest()
(root / "dist/SHA256SUMS").write_text(f"{digest}  {output.name}\n")
print(output)
