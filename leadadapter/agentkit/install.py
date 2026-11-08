"""Explicit project-scoped skill installer; no credentials or global config changes."""
import argparse
import hashlib
import re
import json
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--client', choices=('codex', 'claude', 'grok'), default='codex')
    parser.add_argument('--scope', choices=('project', 'user'), default='project')
    parser.add_argument('--project', default=str(Path.cwd()))
    parser.add_argument('--skill', action='append', default=[])
    args = parser.parse_args(argv)
    base = Path(__file__).parent
    manifest = json.loads((base / 'manifest.json').read_text())
    for relative, digest in manifest.get('files', {}).items():
        if not re.fullmatch(r'skills/[a-z0-9-]+/(SKILL\.md|references/[a-z0-9.-]+)', relative):
            raise ValueError('Invalid agent asset path')
        if hashlib.sha256((base / relative).read_bytes()).hexdigest() != digest:
            raise ValueError('Agent asset checksum mismatch: ' + relative)
    known = {s['name'] for s in manifest['skills']}
    if set(args.skill) - known:
        raise ValueError('Unknown skill')
    selected = [s for s in manifest['skills'] if not args.skill or s['name'] in args.skill]
    root = (Path.home() if args.scope == 'user' else Path(args.project)).resolve()
    target = root / ('.agents' if args.client == 'codex' else '.claude') / 'skills'
    pending = []
    for skill in selected:
        source = base / 'skills' / skill['name']
        for src in sorted(source.rglob('*')):
            if src.is_symlink():
                raise ValueError('Installer refuses source symlinks')
            if src.is_file():
                dest = target / skill['name'] / src.relative_to(source)
                pending.append((dest, src.read_bytes()))
    for dest, content in pending:
        if any(p.is_symlink() for p in (dest, *dest.parents)):
            raise ValueError('Installer refuses target symlinks')
        if dest.exists() and dest.read_bytes() != content:
            raise ValueError('Existing file differs; installer will not overwrite: ' + str(dest))
    for dest, content in pending:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            with dest.open('xb') as handle:
                handle.write(content)
    print(json.dumps({'ok': True, 'client': args.client, 'scope': args.scope, 'directory': str(target), 'skills': [s['name'] for s in selected], 'credentialsWritten': False}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
