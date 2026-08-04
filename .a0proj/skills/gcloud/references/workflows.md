# Cloud Run Operator Workflows

## Contents

1. [Variables and workspace](#variables-and-workspace)
2. [Preflight and snapshot](#preflight-and-snapshot)
3. [Prepare a no-traffic candidate](#prepare-a-no-traffic-candidate)
4. [Validate and apply](#validate-and-apply)
5. [Verify a private candidate](#verify-a-private-candidate)
6. [Approve and execute rollout](#approve-and-execute-rollout)
7. [Rollback](#rollback)
8. [Configuration-only updates](#configuration-only-updates)
9. [New service creation](#new-service-creation)
10. [Failure handling](#failure-handling)

## Variables and workspace

Resolve these values explicitly:

```bash
PROJECT="example-project"
REGION="europe-west1"
SERVICE="example-service"
IMAGE="europe-west1-docker.pkg.dev/example-project/apps/example@sha256:..."
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SNAPSHOT_DIR=".cloud-run-snapshots/${SERVICE}/${TIMESTAMP}"
```

Do not commit `.cloud-run-snapshots/`. Add it to `.gitignore` when the repository policy permits.

Use one command per shell invocation. Avoid shell pipelines for mutating commands so the exact command can be audited and guarded.

## Preflight and snapshot

### Confirm identity and target

```bash
gcloud auth list \
  --filter=status:ACTIVE \
  --format='value(account)'

gcloud projects describe "$PROJECT" \
  --format='yaml(projectId,projectNumber,name)'

gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format='yaml(metadata.name,status.url,status.latestReadyRevisionName,status.traffic,spec.template.spec.serviceAccountName,metadata.annotations)'
```

If `describe` returns Not Found, switch to the new-service workflow. Do not silently create a misspelled service.

### Snapshot service and IAM

```bash
mkdir -p "$SNAPSHOT_DIR"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=export \
  > "$SNAPSHOT_DIR/service.yaml"

gcloud run services get-iam-policy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=yaml \
  > "$SNAPSHOT_DIR/iam.yaml"

gcloud run revisions list \
  --service="$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --sort-by='~metadata.creationTimestamp' \
  --format=yaml \
  > "$SNAPSHOT_DIR/revisions.yaml"
```

Record the snapshot path in the operator report.

## Prepare a no-traffic candidate

Use the exported YAML as the base for an existing service. Do not hand-reconstruct unrelated settings.

### Resolve traffic to explicit revisions

Inspect service status:

```bash
gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format='json(status.traffic,spec.traffic,status.latestReadyRevisionName)'
```

For every current target, write an explicit `revisionName` and preserve its percentage. Remove `latestRevision: true`; otherwise a newly created revision can receive production traffic automatically.

Example desired traffic block:

```yaml
spec:
  traffic:
    - revisionName: example-service-00042-abc
      percent: 100
```

For a split, preserve every explicit revision and exact percentage.

### Name the candidate

Use a deterministic suffix when possible:

```text
<service>-<short-git-sha>
```

Cloud Run revision names must start with the service name, contain lowercase letters, digits, and hyphens, not end in a hyphen, and stay within the platform length limit. Sanitize and shorten before writing `spec.template.metadata.name`.

### Add a zero-percent tag when testing is needed

Add the candidate to `spec.traffic` with `percent: 0` and a lowercase tag:

```yaml
spec:
  template:
    metadata:
      name: example-service-a1b2c3d
  traffic:
    - revisionName: example-service-00042-abc
      percent: 100
    - revisionName: example-service-a1b2c3d
      percent: 0
      tag: candidate-a1b2c3d
```

A tag creates a revision-specific URL. It does not grant public access; the service authentication policy still applies.

### Avoid accidental destructive replacement

Before applying, compare the snapshot and desired manifest. Flag:

- missing containers, environment variables, secret references, volumes, probes, annotations, service account, VPC or Cloud SQL attachments;
- changed ingress or IAM intent;
- reduced limits or scaling changes;
- any `clear`, `remove`, or replacement-style setting not requested;
- any traffic target using `latestRevision: true`;
- any candidate revision with `percent > 0`.

## Validate and apply

### Validate

```bash
gcloud run services replace deploy/cloud-run/service.yaml \
  --dry-run \
  --project="$PROJECT" \
  --region="$REGION"
```

Treat warnings about unsupported fields, missing secret permissions, invalid revision names, probes, or container ports as failures to resolve rather than text to ignore.

### Guard the exact command

Run from the skill directory or use an absolute script path:

```bash
python3 scripts/gcloud_command_guard.py \
  --command "gcloud run services replace deploy/cloud-run/service.yaml --project=$PROJECT --region=$REGION --quiet" \
  --manifest deploy/cloud-run/service.yaml
```

Proceed autonomously only for `ALLOW_AUTONOMOUS`.

### Apply

```bash
gcloud run services replace deploy/cloud-run/service.yaml \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Do not use `--async`; wait for the control-plane result so the agent can verify it.

## Verify a private candidate

### Confirm revision readiness

```bash
gcloud run revisions describe "$CANDIDATE_REVISION" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format='yaml(metadata.name,status.conditions,spec.containers)'
```

Require a Ready condition. A successful CLI exit alone is not sufficient.

### Obtain the tagged URL

```bash
gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format='json(status.traffic)'
```

Find the status traffic item whose tag matches the candidate and use its returned URL.

### Test authenticated access

When direct identity-token invocation is valid for the service:

```bash
TOKEN="$(gcloud auth print-identity-token)"
curl --fail --silent --show-error \
  --header "Authorization: Bearer ${TOKEN}" \
  "${CANDIDATE_URL}${HEALTH_PATH}"
```

Do not print the token. Unset it after use.

When audience or authentication configuration makes direct token testing unreliable, use a local authenticated proxy:

```bash
gcloud run services proxy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --port=8080
```

Manage the proxy process explicitly and stop it after tests.

### Inspect logs

```bash
gcloud run services logs read "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --freshness=30m \
  --limit=200

gcloud run services logs read "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --freshness=30m \
  --log-filter="severity>=ERROR" \
  --limit=100
```

Where needed, filter by revision name with Cloud Logging fields. Verify container startup, startup/liveness probes, ingress binding to `$PORT`, dependency connectivity, and application health.

## Approve and execute rollout

Present one exact rollout proposal:

```text
Current: revision-old=100
Candidate: revision-new=0, tag=candidate-new
Plan: revision-new=10 / revision-old=90; verify; 50/50; verify; 100/0
Abort: failed health check, revision not Ready, new ERROR logs, or defined application threshold
Rollback: revision-old=100
```

Ask for approval of the whole plan and automatic rollback as one bounded authorization.

After approval, execute each stage with explicit project and region:

```bash
gcloud run services update-traffic "$SERVICE" \
  --to-revisions="${CANDIDATE_REVISION}=10,${ROLLBACK_REVISION}=90" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Verify after every stage. Do not proceed merely because the command succeeded.

Move to the next approved percentage only when all checks pass. Do not invent intermediate percentages not included in the approval.

## Rollback

A rollback is a production traffic change. Execute it autonomously only when the earlier approval explicitly authorized automatic rollback to the named revision.

```bash
gcloud run services update-traffic "$SERVICE" \
  --to-revisions="${ROLLBACK_REVISION}=100" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

After rollback:

1. Verify the traffic map.
2. Verify the known-good endpoint.
3. Read current error logs.
4. Leave the failed candidate revision at zero traffic for diagnosis; do not delete it without destructive approval.

## Configuration-only updates

Cloud Run configuration changes create a revision. A direct `gcloud run services update` can unintentionally route traffic to the latest revision when the service traffic target follows `latestRevision`.

Prefer this sequence:

1. Export service YAML.
2. Pin traffic to explicit revisions.
3. Modify only requested configuration.
4. Dry-run with `services replace`.
5. Apply the pinned manifest.
6. Verify the zero-traffic candidate.

Use additive update flags such as `--update-env-vars` or `--update-secrets` only when you have verified that the service does not follow latest traffic and the command cannot remove unrelated settings. Avoid `--set-*` and `--clear-*` without destructive approval.

## New service creation

Create a minimal private service manifest:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: example-service
spec:
  template:
    metadata:
      name: example-service-a1b2c3d
    spec:
      containers:
        - name: ingress
          image: europe-west1-docker.pkg.dev/example-project/apps/example@sha256:...
          ports:
            - containerPort: 8080
```

Add only requested settings and references to existing resources. Do not include IAM policy in the service manifest.

Run `replace --dry-run`, review, and then:

- request approval before creating an explicitly production service because its initial revision will serve service traffic;
- create a non-production private service autonomously after validation;
- request separate approval before public access.

## Failure handling

- **Authentication or permission failure:** report the exact denied permission or role indication; do not broaden IAM automatically.
- **API disabled:** report the prerequisite; do not enable APIs because API enablement is outside scope.
- **Image not found or unauthorized:** stop and report the exact image reference; do not build or push an image.
- **Secret access failure:** identify the secret reference and runtime service account; never read the secret value.
- **Probe/startup failure:** inspect revision conditions and logs; do not route traffic.
- **Manifest drift:** regenerate from the live export and reapply only the requested changes.
- **Unexpected traffic or IAM drift:** stop all mutations and report the live state.
- **Partial rollout failure:** stop at the current approved stage and execute only a pre-authorized rollback.
