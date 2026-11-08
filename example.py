"""Read-only request plan; --live uses an explicitly supplied workspace API key."""
import json, os, sys
from pathlib import Path
from leadadapter import LeadAdapterClient, operations
manifest = json.loads(Path(__file__).with_name('integration.json').read_text())
operation_id = manifest['operationIds'][0]
params = json.loads(os.environ.get('LEADADAPTER_PARAMS', '{}'))
if '--live' in sys.argv:
    if operations[operation_id]['scope'] != 'api:read': raise ValueError('This example executes api:read operations only')
    if 'idempotencyKey' in params: params['idempotency_key'] = params.pop('idempotencyKey')
    if operations[operation_id]['idempotencyRequired'] and not params.get('idempotency_key'): raise ValueError('Supply idempotency_key in LEADADAPTER_PARAMS')
    for name in (operations[operation_id].get('requestSchema') or {}).get('required', []):
        if name not in params.get('body', {}): raise ValueError('Supply body.' + name)
    print(json.dumps(LeadAdapterClient(os.environ['LEADADAPTER_API_KEY']).request(operation_id, **params), indent=2))
else:
    print(json.dumps({'operation_id': operation_id, 'operation': operations[operation_id], 'params': params, 'mode': 'dry-run'}, indent=2))
