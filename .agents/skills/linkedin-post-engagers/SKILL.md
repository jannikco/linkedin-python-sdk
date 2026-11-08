---
name: linkedin-post-engagers
description: Find and qualify people who engaged with a LinkedIn post using LeadAdapter. Use for post engagement research and lead shortlists.
---

# Linkedin Post Engagers

Use the installed LeadAdapter SDK or remote MCP with the user's existing `LEADADAPTER_API_KEY`. Never request an AI model API key for these instructions. Never print credentials or send them to another host.

1. Read [the workflow contract](references/workflow.md) and the installed SDK's capability manifest before selecting operations.
2. Clarify the actual research criteria and connected profile only when missing. Prefer an offline plan or synthetic fixture for setup verification.
3. Execute this chain: **posts.engagers → jobs.wait → prospects.list**. Inspect real receipts; handle unavailable capabilities, queued jobs and approvals explicitly.
4. Require an authorized post URN. Preserve engagement evidence and complete identity URNs. Do not treat engagement as permission to message or enroll anyone.
5. Save private JSON/CSV outputs and a review report outside version control. Report what completed and what remains pending.

For a runnable fixture, use `python -m leadadapter workflows research-to-crm --fixture` or `node lib/cli.mjs workflows research-to-crm --fixture` from a generated repository. Live execution requires explicit `--live` and a private checkpoint path. Review command help before passing write approval flags.

Scope: LinkedIn research and CRM using the caller's authorized LeadAdapter workspace. This skill does not authorize posting, invitations, messages, CRM writes or external account creation merely because it is installed.
