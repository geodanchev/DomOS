# gcloud Command Catalog

Use explicit `--project` and `--region`. Treat examples as patterns; inspect local `--help` when the installed CLI differs.

## Read-only state

```bash
gcloud run services list \
  --project="$PROJECT" \
  --region="$REGION"

gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=export

gcloud run services get-iam-policy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=yaml

gcloud run revisions list \
  --service="$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --sort-by='~metadata.creationTimestamp'

gcloud run revisions describe "$REVISION" \
  --project="$PROJECT" \
  --region="$REGION"
```

## Logs

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
  --log-filter='severity>=ERROR' \
  --limit=100 \
  --format=json
```

## Export, validate, and replace

```bash
gcloud run services describe "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=export \
  > service.yaml

gcloud run services replace service.yaml \
  --dry-run \
  --project="$PROJECT" \
  --region="$REGION"

gcloud run services replace service.yaml \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

For autonomous replacement, require an explicit `spec.traffic` block pinned to existing revision names and a candidate at zero traffic.

## Image-only no-traffic deploy

Use only when a manifest-based dry-run has already validated the equivalent desired state:

```bash
gcloud run deploy "$SERVICE" \
  --image="$IMAGE" \
  --no-traffic \
  --tag="$TAG" \
  --revision-suffix="$SUFFIX" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Do not use `--source` in this skill.

## Traffic — approval required

```bash
gcloud run services update-traffic "$SERVICE" \
  --to-revisions="${NEW_REVISION}=10,${OLD_REVISION}=90" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet

gcloud run services update-traffic "$SERVICE" \
  --to-revisions="${OLD_REVISION}=100" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Never use `--to-latest` autonomously.

## Private local proxy

```bash
gcloud run services proxy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --port=8080
```

## Service-level IAM

Read before writing:

```bash
gcloud run services get-iam-policy "$SERVICE" \
  --project="$PROJECT" \
  --region="$REGION" \
  --format=yaml
```

Grant a named principal only after validating intent:

```bash
gcloud run services add-iam-policy-binding "$SERVICE" \
  --member="serviceAccount:${CALLER_SERVICE_ACCOUNT}" \
  --role='roles/run.invoker' \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Public invocation requires explicit approval:

```bash
gcloud run services add-iam-policy-binding "$SERVICE" \
  --member='allUsers' \
  --role='roles/run.invoker' \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Prefer additive bindings. `set-iam-policy` can remove unrelated bindings and is destructive.

## Existing secret references

Prefer additive updates and pin versions for environment variables:

```bash
gcloud run deploy "$SERVICE" \
  --image="$IMAGE" \
  --no-traffic \
  --update-secrets="DATABASE_PASSWORD=db-password:7" \
  --project="$PROJECT" \
  --region="$REGION" \
  --quiet
```

Do not use `--set-secrets` or `--clear-secrets` without destructive approval. Do not create or read secret values.

## Compose dry-run only by default

```bash
gcloud beta run compose up compose.yaml \
  --dry-run \
  --project="$PROJECT" \
  --region="$REGION"
```

Treat non-dry-run Compose deployment as an explicitly approved exception, not a routine production path.
