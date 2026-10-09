#!/usr/bin/env python3
"""Inventory heurystyczne; wynik wymaga przeglądu kodu, nie jest certyfikatem."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

package = Path(sys.argv[1])
patterns = {
    "http_or_network": r"\b(fetch|XMLHttpRequest|WebSocket|EventSource)\b|sendBeacon|\$\.(ajax|get|post)\s*\(",
    "oauth_credentials": r"oauth|launchWebAuthFlow|access_token|refresh_token|Authorization|client_secret|browser\.identity",
    "obfuscation_or_dynamic_code": r"\beval\s*\(|\bFunction\s*\(|\batob\s*\(|fromCharCode|\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}",
    "filelink": r"cloudFile|onFileUpload|onFileDeleted",
    "markup_or_resource": r"https?://|<script|<iframe|<img|url\s*\(|getComposeDetails|setComposeDetails",
}
with zipfile.ZipFile(package) as archive:
    manifest = json.loads(archive.read("manifest.json"))
    permission_keys = ("permissions", "host_permissions", "optional_permissions", "optional_host_permissions")
    permissions = {key: manifest.get(key, []) for key in permission_keys}
    hosts = []
    for key, values in permissions.items():
        for value in values:
            if value == "<all_urls>" or "://" in value:
                host = urlsplit(value).hostname if value != "<all_urls>" else "*"
                base = (host or "").removeprefix("*.").lower()
                allowed = any(base == d or base.endswith("." + d) for d in ("googleapis.com", "google.com"))
                hosts.append({"field": key, "pattern": value, "outside_google_allowlist": not allowed})
    hits = {key: [] for key in patterns}
    inventory = []
    for item in archive.infolist():
        if item.is_dir():
            continue
        data = archive.read(item)
        inventory.append({"file": item.filename, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if Path(item.filename).suffix.lower() not in (".js", ".html", ".css", ".json", ".svg", ".md"):
            continue
        for number, line in enumerate(data.decode("utf-8").splitlines(), 1):
            for key, pattern in patterns.items():
                if re.search(pattern, line, re.I):
                    hits[key].append({"file": item.filename, "line": number, "text": line})
    result = {"package": package.name, "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
              "manifest": manifest, "permissions": permissions, "network_permissions": hosts,
              "inventory": inventory, "heuristic_matches": hits,
              "limitation": "Regex inventory only. Manual review of every executable/resource file required; absence of matches does not establish safety."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
