# Execution contract

The common workflow is research → completed job → exact identity resolution → reviewed shortlist → approved native CRM promotion → separately approved external sync.

Use `research-to-crm` from the installed SDK. Its contract and source-bound synthetic receipts are bundled with that SDK. A queued receipt is not a result. A completed job can precede prospect ingestion; persist the checkpoint and resume later. Never invent prospect IDs or match people by display name.

Retain full URN namespaces, source evidence, workspace/profile context, selected IDs and write idempotency keys in the private checkpoint. Do not place tokens in it. If a mutation response is lost, stop for reconciliation rather than retrying with another key. A 401 requires valid credentials, 403 requires the relevant permission/capability, and 429 requires respecting Retry-After.

Use raw `.request()` only for a documented operation outside the ergonomic resources. Verify its required body, path, scope and idempotency metadata. MCP tools must come from actual remote tools/list; do not infer MCP tool names from REST operation IDs.
