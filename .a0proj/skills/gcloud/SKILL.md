---
name: cloud-run-operator
description: Operate Google Cloud Run services safely and reproducibly through the gcloud CLI. Use when an agent must inspect, plan, validate, create, deploy, update, diagnose, test, roll out, roll back, or manage revisions, traffic, ingress, service-level IAM, environment configuration, secrets references, probes, scaling, networking attachments, or multi-container Cloud Run services; audit Docker Compose for Cloud Run compatibility; or generate and apply a Cloud Run service YAML. Prefer staged no-traffic revisions, explicit project and region, immutable images, dry-run validation, and auditable snapshots. Do not use for building images, managing Artifact Registry or Cloud Build, provisioning databases, rotating secrets, DNS, Terraform, GitHub Actions, or non-Cloud-Run infrastructure.
---

# Cloud Run Operator

Operate Cloud Run **services** as a guarded control plane. Use `gcloud` from the terminal, preserve current production traffic during normal changes, and make every mutation reproducible and reversible.

## Non-negotiable operating policy

1. Use explicit `--project` and `--region` on every Cloud Run command. Never rely on the active project or default region for mutations.
2. Keep services private by default. Never add `allUsers`, disable the invoker IAM check, or use `--allow-unauthenticated` without explicit approval.
3. Snapshot the current service export and service IAM policy before every mutation to an untracked local directory.
4. Validate a desired service manifest with `gcloud run services replace ... --dry-run` before applying it.
5. For an existing service, preserve the current traffic map by pinning every serving target to explicit revision names. Never leave `latestRevision: true` in an autonomous deployment manifest.
6. Create the candidate revision with zero production traffic and, when useful, a temporary tag for direct testing.
7. Execute routine deploy and configuration updates autonomously only after preflight, snapshot, diff review, and successful dry-run.
8. Request explicit approval before:
   - changing production traffic percentages or sending traffic to a new revision;
   - making a service publicly invokable or widening public exposure;
   - deleting, disabling, clearing, detaching, or otherwise destructively removing resources or configuration.
9. Treat one explicit approval as authorization only for the exact displayed command or rollout plan. Include automatic rollback in the approval request when desired.
10. Never print, store, diff, or commit secret values. Configure only references to existing secrets.
11. Prefer immutable image digests. Accept tags only when the user explicitly chooses tag-based deployment or no digest is available.
12. Stop on an unexpected project, account, region, service identity, traffic map, IAM policy, or manifest diff. Report the mismatch instead of guessing.

## Scope

### In scope

- Cloud Run services, revisions, service logs, service-level IAM, ingress, scaling, concurrency, timeout, CPU/memory, probes, service account, VPC or Cloud SQL attachments, existing Secret Manager references, volumes supported by Cloud Run, container startup order, multi-container services, traffic tags, rollouts, and rollbacks.
- Read-only inspection of prerequisite resources when needed to validate a Cloud Run configuration.
- Docker Compose compatibility analysis and conversion guidance for a single multi-container Cloud Run service.
- Deployment from an already available container image.

### Out of scope

- Building or pushing images; managing Artifact Registry or Cloud Build.
- `gcloud run deploy --source` and Compose deployments that build source or provision non-Cloud-Run resources.
- Provisioning, migrating, backing up, or deleting Cloud SQL or any database.
- Creating or rotating secrets; project-level IAM; API enablement; DNS; load balancers; Cloud Armor; Terraform; CI/CD; GitHub Actions; budgets or billing.
- Cloud Run jobs, worker pools, functions, and multi-region services unless this skill is intentionally extended.

Detect out-of-scope prerequisites, explain exactly what is missing, and stop at the boundary.

## Select the workflow

- **Inspect or diagnose** → follow Read-only inspection.
- **Deploy or update an existing service** → follow Staged revision workflow.
- **Create a new service** → follow New service workflow.
- **Change traffic or roll back** → follow Traffic workflow.
- **Change public access or service IAM** → follow Access workflow.
- **Analyze Compose or a multi-container design** → read `references/compose-and-multicontainer.md` and run `scripts/compose_audit.py` when a Compose file is available.
- **Delete, disable, clear, or detach** → follow Destructive workflow.

Before any mutating command, run `scripts/gcloud_command_guard.py` against the exact command. Follow its classification; never use it as a substitute for inspecting the actual diff.

## Read-only inspection

1. Resolve explicit `PROJECT`, `REGION`, and `SERVICE` from the request, repository configuration, or current resource URL. Ask only when the target cannot be determined safely.
2. Verify terminal context:

```bash
gcloud version
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud projects describe "$PROJECT" --format='value(projectId,projectNumber,name)'
```

3. Inspect the service, IAM policy, revisions, and recent errors with explicit flags. Use the command patterns in `references/command-catalog.md`.
4. Report actual state separately from recommendations. Do not mutate during a diagnostic request unless the user also requested remediation.

## Staged revision workflow

Follow every step in order.

1. **Preflight**
   - Confirm the active account, explicit project, explicit region, service existence, current URL, current service identity, current ingress, and current IAM policy.
   - Resolve the proposed image to a digest when possible.
   - Reject local-only image names such as `app:latest`; require a registry image Cloud Run can pull.

2. **Snapshot**
   - Create a timestamped directory outside tracked source, such as `.cloud-run-snapshots/<service>/<timestamp>/`.
   - Export the service with `--format=export` and save the service IAM policy.
   - Record the currently serving revisions and percentages.

3. **Prepare desired state**
   - Start from the exported service YAML for an existing service.
   - Modify only the requested fields.
   - Assign a deterministic candidate revision name, normally `<service>-<short-git-sha>` when a Git SHA is available.
   - Replace every `latestRevision: true` traffic target with its currently resolved explicit `revisionName`.
   - Preserve all current percentages exactly.
   - Optionally add the candidate revision as a zero-percent tagged target for testing.
   - Keep the service private unless public access was separately approved.

4. **Review the diff**
   - Show a semantic summary: image changes, container changes, resources, environment variable names, secret references, probes, scaling, networking attachments, service account, ingress, IAM, and traffic.
   - Redact values that could be sensitive.
   - Treat unrequested removals as destructive.

5. **Dry-run**

```bash
gcloud run services replace "$MANIFEST" \
  --dry-run \
  --project="$PROJECT" \
  --region="$REGION"
```

6. **Guard and apply**
   - Run the command guard on the exact non-dry-run command and pass the manifest path.
   - Apply autonomously only when the manifest pins production traffic to explicit existing revision names and contains no destructive or public-access change.

```bash
gcloud run services replace "$MANIFEST" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

7. **Verify candidate**
   - Confirm the new revision is Ready.
   - Obtain its tagged URL when present.
   - Test a supplied health endpoint. For a private URL, use an identity token or `gcloud run services proxy` without changing IAM.
   - Read revision/service logs and inspect startup, probe, container, and application errors.
   - Do not migrate production traffic merely because the revision is Ready.

8. **Report**
   - State what changed, the candidate revision, current traffic, test results, and the exact approval needed for rollout.

Read `references/workflows.md` for detailed command sequences and rollback handling.

## New service workflow

1. Require an explicit project, region, service name, ingress container, image reference, and intended privacy model.
2. Use a Cloud Run service YAML and run `replace --dry-run` before creation.
3. Create private by default. Do not add public IAM during service creation.
4. Treat creation of a service explicitly identified as production as a production-traffic decision, because its initial revision becomes the serving revision. Request approval before applying that production creation.
5. A new non-production private service may be created autonomously after a successful dry-run and diff review.
6. Verify the service URL, revision readiness, authentication requirement, and logs.

## Traffic workflow

All `gcloud run services update-traffic` operations require explicit production-traffic approval.

Before asking:

1. Display the current traffic map.
2. Display the proposed map; percentages must total 100.
3. Identify the exact candidate and rollback revision.
4. Show the health checks or evidence already completed.
5. Propose a concrete rollout, for example `10% → verify → 50% → verify → 100%`, and define abort conditions.
6. Ask once for approval of the exact rollout and, optionally, automatic rollback to the named revision.

After approval, execute only the approved stages. Stop and roll back only when rollback was included in the approval; otherwise stop and request approval for the rollback traffic change.

## Access workflow

1. Snapshot the service IAM policy and ingress state.
2. Distinguish network ingress from caller authentication; `ingress=all` does not itself grant unauthenticated invocation.
3. Require explicit approval before any of the following:
   - `--allow-unauthenticated`;
   - adding `allUsers` as `roles/run.invoker`;
   - disabling the invoker IAM check;
   - changing from restricted ingress to broader external ingress when it materially widens exposure.
4. Show the exact principal, role, ingress change, current state, resulting exposure, and rollback command.
5. Prefer additive IAM changes over replacing the entire IAM policy.
6. Treat removal of IAM bindings or narrowing ingress on a serving production service as destructive because it can cause an outage.

## Destructive workflow

Examples include deleting a service or revision, setting service scaling to zero, removing containers, clearing secrets or environment variables, replacing IAM policy, detaching VPC or Cloud SQL connections, clearing volumes, or removing a serving revision from traffic without an approved traffic plan.

Before execution:

1. Snapshot all affected Cloud Run configuration and IAM.
2. List exactly what will be removed and the user-visible impact.
3. State whether recovery is possible and how.
4. Request explicit approval for the exact command.
5. Re-run the command guard after approval and execute only that command.

## Compose and multi-container rules

Read `references/compose-and-multicontainer.md` before converting or deploying Compose.

Use Compose primarily as an analysis and migration input. Run:

```bash
python3 scripts/compose_audit.py path/to/compose.yaml --format markdown
gcloud beta run compose up path/to/compose.yaml \
  --dry-run \
  --project="$PROJECT" \
  --region="$REGION"
```

Do not run a production `compose up` autonomously. Compose deployment is a pre-GA workflow, can translate only a subset of features, can shift service traffic, and can provision other Google Cloud resources. Convert the intended Cloud Run state into a reviewed service YAML instead.

## Runtime freshness rule

The gcloud CLI evolves. Before using a flag not covered by this skill, or after a CLI upgrade, inspect local help:

```bash
gcloud run deploy --help
gcloud run services replace --help
gcloud run services update-traffic --help
```

Prefer generally available commands. Clearly label alpha, beta, preview, or pre-GA behavior and avoid production dependency on it unless the user explicitly accepts that risk.

## Output contract

After each operation, use the structure in `references/output-contract.md`. Always include:

- target account/project/region/service;
- operation classification;
- snapshot location;
- dry-run result;
- applied command or reason it was not applied;
- candidate revision and readiness;
- current production traffic and public-access state;
- verification evidence;
- rollback path;
- exact pending approval, if any.

## Bundled resources

- `scripts/gcloud_command_guard.py` — classify a proposed gcloud command under this approval policy.
- `scripts/compose_audit.py` — produce a static Cloud Run compatibility audit for Compose.
- `references/workflows.md` — detailed staged deploy, verification, rollout, and rollback procedures.
- `references/compose-and-multicontainer.md` — mapping and architecture constraints.
- `references/command-catalog.md` — safe command patterns.
- `references/output-contract.md` — consistent operator report format.
- `references/sources.md` — official documentation used to ground the skill and refresh volatile details.
