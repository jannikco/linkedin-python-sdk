# LeadAdapter Python API client

Standard-library Python client for the LeadAdapter REST API.

Maintainer: jannikco · License: MIT · Verification: **mock-only**

## Quick start

Requires Python 3.10 or later. Node.js 22 is optional for the npm compatibility wrapper.

```sh
python3 -m unittest test_sdk.py
python3 example.py --dry-run
# Optional: install this repository as a local Python package
python3 -m pip install .
```

The default example runs locally without credentials and makes no external changes. Verification status describes recorded evidence; local configuration tests do not establish that provider authentication or execution works.

## Authorized execution

Selected operation IDs: list_leads_get. Review integration.json and leadadapter/operations.json for exact paths, scopes and parameters. Set LEADADAPTER_API_KEY and optionally LEADADAPTER_PARAMS (JSON with path, query or body), then run python3 example.py --live. The example only executes operations classified api:read, including LinkedIn POST read requests. POST reads require an explicit idempotencyKey in LEADADAPTER_PARAMS. Replace example identifiers with authorized account data before live execution. Pending jobs, approvals and capability availability depend on your workspace and connected account.

## Managed service

[Continue with LeadAdapter](https://leadadapter.com/register?utm_source=github&utm_campaign=github-linkedin-python-sdk). This repository is maintained by the integration team and does not imply endorsement by LinkedIn or other providers.

## Provenance and support

Source revision: ea33908e4d5e10508739f28e11abf708e11f3117f1108b904229eeeb00079e55. The complete manifest is in integration.json; SHA256SUMS covers the reviewed artifact. Open a repository issue without credentials or personal data. See SECURITY.md for sensitive reports. No telemetry is sent by this code; signup links include explicit campaign parameters.

## Example request parameters

The following is illustrative input for the first selected operation. Replace example identifiers with data you are authorized to use and choose a unique idempotency key per new request. The default example does not send this request.

```json
{}
```

Set LEADADAPTER_PARAMS to your edited JSON when explicitly running --live. Keep the same idempotency key only when retrying the same logical request.
