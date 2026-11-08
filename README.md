# LinkedIn Python SDK — LeadAdapter

**Bring LinkedIn research and lead workflows into Python with a standard-library client.**

Use LeadAdapter from Python scripts, data pipelines and agent services. The public client includes operation metadata from the pinned API contract, explicit request parameters and a job-polling helper; runtime dependencies are limited to Python’s standard library.

[Create your LeadAdapter account](https://leadadapter.com/github/start?integration=linkedin-python-sdk&utm_source=github&utm_campaign=github-linkedin-python-sdk&utm_content=readme) · [See plans and pricing](https://leadadapter.com/pricing) · [API documentation](https://leadadapter.com/docs/api?lang=en) · [Full API reference](https://leadadapter.com/docs/api-reference?lang=en)

## Built for coding agents

[Download SDKs and the agent kit from GitHub Releases](https://github.com/jannikco/linkedin-api/releases/latest).

Use this API from **Claude Code, Codex or Grok Build** in your current coding session. Install the skills into the project where you are building:

```sh
python3 -m leadadapter agents install --client codex --scope project --project /path/to/your/project
# Replace codex with claude or grok for that client.
```

No additional AI model key is needed. Live LinkedIn operations use your **LeadAdapter API key** and connected account permissions. Installation never writes credentials or overwrites conflicting files.

Ask your agent: “Research B2B software founders, produce a shortlist with evidence, and wait for my review before adding anyone to CRM.”

### Run a complete workflow now

```sh
python3 -m leadadapter workflows research-to-crm --fixture
```

Then follow the [research → review → CRM cookbook](docs/research-to-crm.md) for authorized live reads and reviewed CRM handoff. [capabilities.json](capabilities.json) and [llms.txt](llms.txt) provide concise machine-readable discovery. The SDK keeps its raw request API alongside task-level resources. Five runnable task recipes are included in examples/: people research, post engagers, profile enrichment, reviewed CRM handoff and existing CRM sync. Run each without flags for a plan; --fixture uses synthetic receipts. Live mutation recipes require explicit approvals and caller-supplied stable idempotency keys.

## What you can build

- Read captured leads into an internal reporting pipeline.
- Request profile research and inspect terminal job results.
- Connect lead qualification scripts to existing LeadAdapter CRM records.

Built for: Python developers, data teams and builders of sales research agents.

## Start with one LeadAdapter API key

Create or sign in to [LeadAdapter](https://leadadapter.com/github/start?integration=linkedin-python-sdk&utm_source=github&utm_campaign=github-linkedin-python-sdk&utm_content=readme), choose an owned workspace, complete required onboarding, and create a workspace API key under **Settings → API keys**. The only service credential required by this repository is `LEADADAPTER_API_KEY`.

Use a key with `api:read` for these examples. Fresh LinkedIn research needs a connected profile, supported execution access and required consent; your plan’s allowances apply. For a workspace with multiple profiles, add the documented `profile_id` to select one.

### Your first useful API call

Read your existing lead data with one workspace key. The Python client returns response dictionaries so you can inspect the actual API receipt.

```sh
export LEADADAPTER_API_KEY="YOUR_WORKSPACE_API_KEY"
```

```sh
curl --fail-with-body --silent --show-error \
  "https://leadadapter.com/api/v1/leads?per_page=10" \
  -H "Authorization: Bearer $LEADADAPTER_API_KEY" \
  -H "Accept: application/json"
```

The response uses LeadAdapter’s envelope: `ok`, `data`, governance context and request/action identifiers where available. Inspect the actual response; the pinned schema intentionally does not invent a universal lead, profile or search-result shape.

### Use the Python client

Requires Python 3.10+. Clone this repository; the included `leadadapter` package runs from the project directory without third-party runtime dependencies:

```sh
git clone https://github.com/jannikco/linkedin-python-sdk.git
cd linkedin-python-sdk
export LEADADAPTER_API_KEY="YOUR_WORKSPACE_API_KEY"
```

```python
import os
from leadadapter import LeadAdapterClient

client = LeadAdapterClient(os.environ["LEADADAPTER_API_KEY"])
receipt = client.request("list_leads_get", query={"per_page": 10})
print(receipt)
```
## What the full LeadAdapter platform covers

This repository focuses on the reusable client. Your LeadAdapter account also provides the following documented API surfaces; account access, adapter support and operation prerequisites apply.

| Capability | Build this | Documented API routes | Execution considerations |
| --- | --- | --- | --- |
| People and post discovery | Research prospects and relevant conversations | `POST /linkedin/searches/people`<br>`POST /linkedin/searches/posts` | Fresh retrieval needs a connected, supported executor. |
| Company research | Build account context and inspect known company pages | `POST /linkedin/searches/companies`<br>`GET /linkedin/companies`<br>`POST /linkedin/company-enrichments` | Company-voice operations require the relevant page-admin rights. |
| Profile enrichment | Add visible professional context to selected leads | `POST /linkedin/profile-enrichments` | Allowance, profile-view budget and returned coverage apply; email availability is conditional. |
| Post engagement | Research the people engaging with a selected post | `POST /linkedin/post-engager-requests` | Results depend on what the connected account and adapter can retrieve. |
| Leads and export | Read, qualify and move captured lead data | `GET /leads`<br>`GET /leads/export` | Workspace-scoped data; pagination is explicit. |
| Native CRM | Work with companies, pipelines, stages, deals and tasks | `GET /crm/{entity}`<br>`POST /crm/{entity}`<br>`GET /crm/{entity}/records` | Write scopes and entity-specific inputs apply. |
| Stored content and publishing | Connect editorial review and scheduled publishing | `GET /content-posts`<br>`GET /scheduled-posts`<br>`POST /scheduled-posts` | Queued or scheduled work is distinct from confirmed publication. |
| Messages and connections | Build reviewed conversation and connection workflows | `GET /messages`<br>`POST /linkedin/messages`<br>`POST /linkedin/connection-requests` | Outbound actions remain capped, permissioned and subject to applicable approval. |
| Engagement actions | Prepare relevant comments and reactions | `POST /linkedin/comments`<br>`POST /linkedin/post-reactions` | Writes require the appropriate scope and governance acceptance. |
| Comment-to-lead workflows | Connect a comment keyword to a controlled follow-up process | `GET /automations`<br>`POST /automations` | Supported triggers are comment_keyword and any_comment; DM prerequisites and limits apply. |
| Lead pages and tracked links | Connect campaigns with lead capture and tracked assets | `GET /lead-pages`<br>`GET /links` | Publication and asset management are separate governed operations. |
| Approvals and audit | Review proposed actions and understand execution decisions | `GET /approvals`<br>`POST /approvals/{approval_id}/decisions`<br>`GET /actions` | Approval does not override caps or unavailable capabilities. |
| Webhooks | React to supported lead, comment, message and approval events | `GET /webhooks`<br>`POST /webhooks`<br>`GET /webhooks/{id}/deliveries` | Configure subscriptions and validate signed deliveries in your receiver. |
| Sales intelligence | Connect research with business context and reviewable opportunities | `GET /signals`<br>`GET /sales-opportunities`<br>`GET /business-context` | Availability follows the account’s configured features and existing records. |

## Operations highlighted in this repository

| Operation ID | HTTP route, relative to `/api/v1` | Required scope |
| --- | --- | --- |
| `list_leads_get` | `GET /leads` | `api:read` |

The SDK additionally includes all 134 operations from its pinned OpenAPI contract. Use the [API reference](https://leadadapter.com/docs/api-reference?lang=en) for complete inputs, limits and operation behavior.

## Fresh data, queued jobs and reliable outcomes

Stored workspace data can return immediately. Fresh LinkedIn retrieval or outbound work may return a job receipt, including `job_id`, instead of a completed result. When a job is returned:

1. Keep its identifier and the request’s idempotency key.
2. Poll `GET /api/v1/jobs/{job_id}` with the same workspace key. A documented `wait=true` can hold the read for up to25 seconds.
3. Inspect the terminal status and result/error: `done`, `failed` or `cancelled`. `queued` and `leased` are still in progress.

```sh
export JOB_ID="REPLACE_WITH_RETURNED_JOB_ID"
curl --fail-with-body --silent --show-error \
  "https://leadadapter.com/api/v1/jobs/$JOB_ID?wait=true" \
  -H "Authorization: Bearer $LEADADAPTER_API_KEY" \
  -H "Accept: application/json"
```

The SDK provides `wait_for_job` to poll a job. It can return a failed or cancelled terminal receipt; inspect the returned status and error. An accepted request, an approved action and confirmed LinkedIn delivery are separate states. Do not report successful delivery from a queue acknowledgement.

## Permissions and operational control

- **One workspace key, explicit scopes.** Use `api:read` for the documented reads, and grant write access only for the operations your application needs. Store keys server-side; do not place them in browser bundles, commits or issue reports.
- **Connected-account execution.** Browser-mode work uses the user’s connected browser. Supported consented cloud operations can run independently of Chrome. Availability is checked per operation; an API route does not grant unrestricted LinkedIn access.
- **Governed actions.** Workspace/profile caps, pacing, do-not-engage rules, account permissions and required approvals still apply. Some operations support `dry_run`; check the operation’s schema before sending it.
- **Explicit retries.** Operations requiring `Idempotency-Key` include fresh-data POST reads as well as writes. Reuse the same key and payload for the same logical request. Resolve uncertain outcomes before issuing a new request.
- **Useful errors.** Handle permission/capability refusals, validation errors and429 pacing responses. Preserve request identifiers for support and follow any returned retry guidance.

## Public client, private service

This repository publishes client code under MIT. LeadAdapter’s hosted application, connected-account execution, governance, data storage and commercial service remain private. The public code does not include the service backend or a self-hosted substitute for a LeadAdapter account. This is an independent LeadAdapter integration, not an official LinkedIn API or LinkedIn-endorsed SDK.

## Continue building

- [Activate this workflow in LeadAdapter](https://leadadapter.com/github/start?integration=linkedin-python-sdk&utm_source=github&utm_campaign=github-linkedin-python-sdk&utm_content=readme) — the selected project and repository campaign stay with your signup.
- [Plans and pricing](https://leadadapter.com/pricing) — check current feature access and allowances before production use.
- [TypeScript SDK](https://github.com/jannikco/linkedin-typescript-sdk), [Python SDK](https://github.com/jannikco/linkedin-python-sdk) and [MCP server](https://github.com/jannikco/linkedin-mcp).
- [API quickstart](https://leadadapter.com/docs/api?lang=en), [complete reference](https://leadadapter.com/docs/api-reference?lang=en), [MCP guide](https://leadadapter.com/docs/mcp?lang=en) and [public OpenAPI](https://leadadapter.com/api/v1/openapi.json).
- [Integration directory](https://jannikco.github.io/pipmcp-connectors/integrations/linkedin/).

## Verification and support

This code is checked with contract fixtures; the MCP artifact also tests stdio tools/call. These checks establish client behavior, not live LinkedIn provider execution or conversion outcomes. See `integration.json` and `SHA256SUMS` for the recorded artifact evidence. The source contract is [LeadAdapter’s public OpenAPI](https://leadadapter.com/api/v1/openapi.json).

For a reproducible client bug, open a repository issue with the operation ID and a sanitized request identifier. For account access, plans or execution availability, use LeadAdapter’s in-app support. Never include API keys, personal lead data or session material.
