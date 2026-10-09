#!/usr/bin/env python3
"""Check Git's publication set without printing matched secret values."""
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
patterns = [
    r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'\bgh[pousr]_[A-Za-z0-9]{20,}\b',
    r'\bgithub_pat_[A-Za-z0-9_]{20,}\b',
    r'\bGOCSPX-[A-Za-z0-9_-]{15,}\b',
    r'\bya29\.[A-Za-z0-9_-]{20,}\b',
    r'\b1//[A-Za-z0-9_-]{25,}\b',
    r'[/]Users[/][^/\s]+[/]',
]
for name in filter(None, names):
    if name.endswith('.conf') or name.startswith(('audit/evidence/', 'audit/extracted/', 'local/', 'dist/')) or Path(name).name == 'runtime.json':
        raise SystemExit(f'Forbidden publication file: {name}')
    data = subprocess.check_output(['git', 'show', ':' + name], cwd=root).decode('utf-8')
    if any(re.search(pattern, data) for pattern in patterns):
        raise SystemExit(f'Potential secret or local identity in {name}; inspect privately before publishing.')
print(f'PASS: publication scan ({len(list(filter(None, names)))} files); no matched secrets/local paths.')
