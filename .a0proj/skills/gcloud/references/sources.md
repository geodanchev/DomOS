# Official Reference Sources

Use current Google Cloud documentation and the installed gcloud help as the source of truth. The following pages grounded this skill and should be rechecked when behavior changes:

- Cloud Run deploy command: https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy
- Replace service from YAML and dry-run: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/replace
- Describe/export service: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/describe
- Update traffic: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update-traffic
- Service logs: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/logs/read
- Revision management: https://docs.cloud.google.com/run/docs/managing/revisions
- Deploying and multi-container services: https://docs.cloud.google.com/run/docs/deploying
- Container configuration and startup order: https://docs.cloud.google.com/run/docs/configuring/services/containers
- Authentication overview: https://docs.cloud.google.com/run/docs/authenticating/overview
- Public access: https://docs.cloud.google.com/run/docs/authenticating/public
- Secret configuration: https://docs.cloud.google.com/run/docs/configuring/services/secrets
- Cloud Run Compose: https://cloud.google.com/run/docs/deploy-run-compose
- Compose CLI: https://docs.cloud.google.com/sdk/gcloud/reference/beta/run/compose/up

Volatile behavior:

- Cloud Run Compose is pre-GA and the CLI group is beta as of July 2026.
- Readiness probes and other preview features can change.
- gcloud flags can be added, renamed, or promoted between release tracks.

Before relying on volatile behavior, run the relevant local `gcloud ... --help` and prefer the generally available command when equivalent.
