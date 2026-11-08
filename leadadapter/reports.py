"""Private workflow export files. Export is explicit and never writes credentials."""
import csv
import io
import json
import os
import tempfile
from pathlib import Path

def write_report(result, filename):
    target = Path(filename).absolute()
    if target.suffix != '.json':
        raise ValueError('Report output must end in .json')
    outputs = [target, target.with_suffix('.csv'), target.with_suffix('.review.md')]
    for path in outputs:
        if path.exists() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('Report output exists or contains a symlink; choose a new private path')
    rows = result.get('prospects') or result.get('candidates') or []
    def safe(value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return "'" + text if text.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else text
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(['prospect_id', 'lead_id', 'identities'])
    for row in rows:
        writer.writerow([safe(row.get(k, '')) for k in ['prospect_id', 'lead_id', 'identities']])
    report = '# Research review\n\nStatus: ' + str(result.get('status', 'unknown')) + '\n\n'
    report += str(len(rows)) + ' source-matched candidates. Inspect the JSON evidence and exact IDs before approving promotion.\n\n'
    report += 'Destination: ' + str(result.get('destination', 'leadadapter-native-crm')) + '\n\n'
    report += 'An export is not a review approval or proof of live LinkedIn execution. Uncertain writes require reconciliation.\n'
    contents = [json.dumps(result, indent=2, ensure_ascii=False) + '\n', stream.getvalue(), report]
    target.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for path, content in zip(outputs, contents):
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
                handle.write(content)
        return [str(p) for p in outputs]
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
