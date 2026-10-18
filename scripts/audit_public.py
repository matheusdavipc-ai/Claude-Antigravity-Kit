"""Fail on private artifacts and recognizable credentials before publishing."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {'.credentials.json','.env','storage.sqlite','server.env','installation.json','migration.json','openrouter.dpapi'}
FORBIDDEN_DIRS = {'secrets','backups','runs','projects','node_modules'}
PATTERNS = [
    re.compile(r'\bsk-(?:or-v1-|ant-)[A-Za-z0-9_-]{15,}'),
    re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'(?i:[A-Z]:[/\\]Users[/\\](?!PUBLIC\b)[\w.-]+)|/Users/[\w.-]+'),
    re.compile(r'(?i)\b(?:dg-promotora|lm-consultoria-imobili[aá]ria|Site Coding)\b'),
]

def audit(root=ROOT):
    findings = []
    for file in root.rglob('*'):
        relative = file.relative_to(root)
        if any(p in ('.git','__pycache__','.pytest_cache') for p in relative.parts):
            continue
        if file.is_symlink():
            findings.append({'file': str(relative), 'reason': 'symlink in public bundle'})
            continue
        if not file.is_file(): continue
        if file.name in FORBIDDEN_NAMES or any(p in FORBIDDEN_DIRS for p in relative.parts):
            findings.append({'file': str(relative), 'reason': 'private runtime artifact'})
            continue
        try: text = file.read_text(encoding='utf-8')
        except UnicodeError:
            findings.append({'file': str(relative), 'reason': 'unreviewed binary'})
            continue
        # The scanner contains generic detection patterns, not actual credentials.
        if relative.as_posix() == 'scripts/audit_public.py': continue
        for index, pattern in enumerate(PATTERNS):
            if pattern.search(text):
                findings.append({'file': str(relative), 'reason': 'sensitive pattern ' + str(index+1)})
    return findings

if __name__ == '__main__':
    findings = audit()
    print(json.dumps({'passed': not findings, 'findings': findings}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if findings else 0)
