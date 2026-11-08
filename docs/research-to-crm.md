# Build a reviewed pipeline from LinkedIn research

Use the SDK's task-level resources instead of manually constructing HTTP requests. The same account access, caps and permissions apply as in LeadAdapter.

## Prove the workflow locally

```sh
python3 -m leadadapter workflows research-to-crm --fixture --output /private/path/fixture-report.json
python3 -m leadadapter workflows research-to-crm --keywords "B2B software"
```

The fixture exercises queued reads, completion and exact prospect identity resolution against synthetic responses. The second command prints a plan without network access.

## Run authorized research

Set LEADADAPTER_API_KEY in your shell environment without placing it in source. Choose a private checkpoint path.

```sh
python3 -m leadadapter workflows research-to-crm --keywords "B2B software" --live --checkpoint /private/path/research.json
```

Add --output /private/path/report.json to export private JSON, CSV and a Markdown review report. Output files are never overwritten. Review the resulting shortlist and source evidence. If prospect ingestion is pending, rerun with the same checkpoint after it completes. Select exact returned IDs before promotion:

```sh
python3 -m leadadapter workflows research-to-crm --keywords "B2B software" --live --checkpoint /private/path/research.json --prospect-id ACTUAL_REVIEWED_ID --approve-promote
```

Promotion adds the reviewed person to native LeadAdapter CRM. To sync a configured external CRM, add `--provider hubspot --approve-crm` only after reviewing the destination. The SDK does not provision accounts.

## More tasks

Use people.search, profiles.enrich, posts.engagers, prospects.list/get/promote, leads.list/export, crm.sync_lead and jobs.wait. POST reads require explicit stable idempotency keys. Raw request() and the existing job poller remain available. See generated type definitions and operation metadata for exact inputs.

## Receipt handling

401: fix credentials. 403: inspect scopes/capabilities and connected profile. 422: correct the actual input schema. 429: respect Retry-After. Queued/running is pending, not success. A completed search can precede prospect ingestion. Never match names alone or discard URN namespaces. Unknown write outcomes require reconciliation with stored keys.
