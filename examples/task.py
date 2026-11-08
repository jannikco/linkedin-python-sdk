"""Five task recipes: offline plan by default, then explicit fixture or authorized live execution."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from leadadapter import LeadAdapterClient

TASKS = ['people-research', 'post-engagers', 'profile-enrichment', 'reviewed-crm-handoff', 'existing-crm-sync']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=TASKS)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fixture', action='store_true')
    group.add_argument('--live', action='store_true')
    parser.add_argument('--approve-promote', action='store_true')
    parser.add_argument('--approve-crm', action='store_true')
    args = parser.parse_args()
    write = args.task in TASKS[3:]
    if not args.fixture and not args.live:
        print(json.dumps({'task': args.task, 'mode': 'plan', 'credential': 'LEADADAPTER_API_KEY', 'networkRequests': 0, 'mutationApprovalRequired': write}, indent=2))
        return
    values = json.loads(os.environ.get('LEADADAPTER_TASK_INPUT', '{}'))
    if args.fixture and not values:
        values = {'keywords':['synthetic fixture'], 'post_urn':'urn:li:activity:fixture', 'public_id':'fixture-person', 'prospect_id':'fixture-prospect-1', 'lead_id':'fixture-lead-1', 'provider':'hubspot', 'idempotency_key':'fixture-' + args.task}
    key = values.get('idempotency_key')
    if not key:
        parser.error('Supply a stable idempotency_key in LEADADAPTER_TASK_INPUT')
    if write and not (args.approve_promote if args.task == TASKS[3] else args.approve_crm):
        parser.error('Review exact target IDs and explicitly approve this mutation')
    contract = json.loads((Path(__file__).parent.parent / 'leadadapter' / 'workflow-contract.json').read_text())
    def transport(url, method, headers, body, timeout):
        receipts = contract['receipts']
        receipt = receipts['completed'] if '/jobs/' in url else receipts['promoted'] if '/promotions' in url else receipts['synced'] if '/crm-syncs' in url else receipts['queued']
        return (202 if receipt.get('job_id') else 200), {'Content-Type':'application/json'}, json.dumps(receipt).encode()
    client = LeadAdapterClient('synthetic-fixture-key', transport=transport) if args.fixture else LeadAdapterClient(os.environ['LEADADAPTER_API_KEY'])
    profile = values.get('profile_id')
    if args.task == TASKS[0]:receipt = client.people.search(values['keywords'], idempotency_key=key, profile_id=profile)
    elif args.task == TASKS[1]:receipt = client.posts.engagers(values['post_urn'], idempotency_key=key, profile_id=profile)
    elif args.task == TASKS[2]:receipt = client.profiles.enrich(public_id=values.get('public_id'), linkedin_urn=values.get('linkedin_urn'), lead_id=values.get('lead_id'), include_email=False, idempotency_key=key, profile_id=profile)
    elif args.task == TASKS[3]:receipt = client.prospects.promote(values['prospect_id'], idempotency_key=key, approved=True, profile_id=profile)
    else:receipt = client.crm.sync_lead(values['lead_id'], provider=values['provider'], idempotency_key=key, approved=True, profile_id=profile)
    if not write and receipt.get('job_id'):receipt = client.jobs.wait(receipt['job_id'])
    print(json.dumps({'task':args.task, 'mode':'fixture' if args.fixture else 'live', 'receipt':receipt, 'providerExecution':'not-run' if args.fixture else 'inspect-receipt'}, indent=2))

if __name__ == '__main__':main()
