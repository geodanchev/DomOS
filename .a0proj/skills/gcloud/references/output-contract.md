# Operator Output Contract

Use this format after a Cloud Run operation. Keep actual state and proposed state distinct.

```markdown
# Cloud Run operation

## Target
- Account: ...
- Project: ...
- Region: ...
- Service: ...
- Environment: production / staging / development / unknown

## Classification
- Mode: read-only / autonomous staged mutation / confirmation required / blocked out of scope
- Approval category: none / production traffic / public access / destructive

## Before
- Service URL: ...
- Ready revision: ...
- Traffic: revision-a=100
- Ingress: ...
- Invocation: private/public
- Runtime service account: ...
- Snapshot: ...

## Requested change
- Images: container old → new digest
- Configuration: ...
- Sensitive values: redacted; secret references only
- Unrequested removals: none / list

## Validation
- Compose audit: pass / warnings / blockers / not applicable
- Semantic diff: pass / concerns
- `services replace --dry-run`: pass / fail
- Guard classification: ...

## Applied
- Command: ...
- Result: applied / not applied
- Candidate revision: ...
- Candidate traffic: 0%
- Candidate tag URL: ...

## Verification
- Revision Ready: yes/no
- Health test: ...
- Logs: ...
- Production traffic unchanged: yes/no
- Public access unchanged: yes/no

## Rollback
- Known-good revision: ...
- Rollback command: ...
- Pre-authorized: yes/no

## Pending approval
- None, or one exact approval request with command/rollout, impact, and rollback.
```

Rules:

- Never include access tokens, passwords, secret payloads, or full sensitive environment values.
- Include exact absolute target identifiers; do not write only “current project.”
- Quote the exact command requiring approval.
- For traffic approval, show the full before/after percentage map and total 100%.
- For public access, state whether both ingress and unauthenticated invocation are changing.
- For destructive approval, list every removed item and recovery limit.
