# Docker Compose and Multi-container Cloud Run

## Contents

1. [Use Compose as migration input](#use-compose-as-migration-input)
2. [Cloud Run service model](#cloud-run-service-model)
3. [Ingress and routing](#ingress-and-routing)
4. [Container communication](#container-communication)
5. [Lifecycle and scaling](#lifecycle-and-scaling)
6. [Startup order and health checks](#startup-order-and-health-checks)
7. [Storage and state](#storage-and-state)
8. [Security and secrets](#security-and-secrets)
9. [Compose mapping rules](#compose-mapping-rules)
10. [Reverse proxy migration](#reverse-proxy-migration)
11. [Recommended conversion process](#recommended-conversion-process)

## Use Compose as migration input

Cloud Run Compose is a pre-GA convenience workflow. It translates a subset of Compose into one Cloud Run service containing multiple containers. It is useful for discovery, dry-run validation, and development migration, but it is not the preferred production control surface for this skill.

Default behavior for this skill:

1. Audit the Compose file statically.
2. Run `gcloud beta run compose up ... --dry-run` when the local CLI supports it.
3. Explain unsupported or dangerous semantics.
4. Generate a reviewed `serving.knative.dev/v1` service YAML.
5. Apply the service YAML through the staged revision workflow.

Do not execute production `compose up` autonomously. It can shift traffic and can provision Cloud Storage or Secret Manager resources, which crosses this skill's infrastructure boundary.

## Cloud Run service model

A multi-container Cloud Run service has:

- one ingress container receiving incoming requests;
- zero or more sidecars, up to the platform total of ten containers per instance;
- one shared instance lifecycle;
- one shared network namespace;
- one service-level traffic policy, ingress setting, and invocation IAM policy;
- one scaling decision that creates or removes the whole container set together.

Use one service when containers must deploy, scale, and roll back together and share the same security boundary. Use separate services when they need independent scaling, lifecycle, traffic, identity, or failure isolation. This skill can identify that architectural need but does not automatically split services without explicit intent.

## Ingress and routing

Only one container may declare the Cloud Run ingress `containerPort`. That container must listen on `0.0.0.0` at the injected `PORT` value or the configured ingress port.

Cloud Run terminates external TLS. An internal reverse proxy should normally listen on plain HTTP inside the instance. Remove container-managed ACME certificate issuance, port 443 exposure, HTTP-to-HTTPS redirect listeners, and persistent certificate files unless there is an exceptional, explicitly reviewed design.

For same-origin frontend and API routing, reasonable patterns include:

- frontend Nginx as ingress, serving static files and proxying `/api` to a backend sidecar;
- Traefik as ingress with static or file-based configuration;
- an application gateway container with explicit routes.

Do not depend on Docker labels or Docker daemon discovery inside Cloud Run.

## Container communication

Containers in the same instance can communicate over localhost and can also use container names where supported by the platform configuration. Prefer explicit unique ports:

```text
ingress: 8080
frontend sidecar: 3000
backend sidecar: 8000
```

Do not create a Docker bridge network. Do not assume Compose DNS, aliases, or network isolation semantics create security boundaries inside one Cloud Run instance.

## Lifecycle and scaling

All containers in a service instance start and stop as one unit. If the service scales to five instances, Cloud Run creates five copies of every container.

Consequences:

- sidecars cannot scale independently;
- a heavy reverse proxy, worker, or database sidecar multiplies with every instance;
- each container must fit within the configured resource model;
- failures in a required sidecar can make the whole revision unhealthy;
- `restart:` policies are not used; Cloud Run controls instance lifecycle.

Treat a component that needs independent scaling or durable singleton semantics as a separate prerequisite or service design decision.

## Startup order and health checks

Map Compose `depends_on` to Cloud Run container startup dependencies only when startup order is genuinely required. Configure startup probes on dependencies; order alone does not prove readiness.

Translate Compose health checks deliberately:

- startup readiness dependency → startup probe;
- process recovery need → liveness probe;
- request eligibility → readiness probe when the selected Cloud Run feature level supports it;
- application smoke test → post-deployment external test.

Do not copy `depends_on: condition: service_healthy` blindly. Validate each command, port, timeout, and expected response in the Cloud Run container environment.

## Storage and state

Cloud Run instances are ephemeral and may be replaced or multiplied. Do not run a production relational database with its data directory on an instance filesystem or a generic Cloud Storage mount.

Block or redesign:

- PostgreSQL, MySQL, MariaDB, MongoDB, or similar database containers with persistent local volumes;
- Docker named volumes used as durable POSIX storage;
- host bind mounts;
- `/var/run/docker.sock`;
- certificate or operational log files that must survive instance replacement.

Use stdout/stderr for logs. Treat external databases and durable storage as existing prerequisites. This skill may attach a Cloud Run service to an existing Cloud SQL instance but must not provision or administer that instance.

In-memory shared volumes can be appropriate for temporary inter-container files. Review size and memory accounting.

## Security and secrets

- Keep invocation private by default.
- Use a dedicated runtime service account where appropriate.
- Reference existing Secret Manager secrets; never put plaintext secret values into Compose, YAML, command history, or reports.
- Pin secret versions for environment-variable injection when reproducibility matters; use volume semantics only when the application requires file access or rotation behavior.
- Do not expose proxy dashboards or administrative ports publicly.
- Do not use privileged mode, devices, host PID/IPC/network, Linux capability expansion, or Docker sockets.
- Treat service-level IAM and ingress as shared by all containers in the service.

## Compose mapping rules

| Compose construct | Cloud Run treatment |
|---|---|
| `services` | Containers in one Cloud Run service when using Compose translation |
| one service with `ports` or Cloud Run ingress extension | Candidate ingress container; only one is allowed |
| `expose` | Internal sidecar port documentation; verify unique ports |
| `build` | Out of this skill's production scope; require a prebuilt image |
| `image` | Prefer registry digest; reject local-only image names |
| `depends_on` | Map to startup dependencies plus startup probes |
| `healthcheck` | Translate deliberately to Cloud Run probes and smoke tests |
| `restart` | Remove; Cloud Run manages lifecycle |
| `container_name` | Remove or treat as descriptive only |
| bridge `networks` | Remove; containers share the instance network |
| Docker labels | Do not rely on them for Cloud Run routing |
| named/bind volumes | Review; block durable database data and host mounts |
| top-level secret files | Do not let production Compose auto-create secrets; reference existing secrets |
| `deploy.replicas` | Not a direct Cloud Run scaling model; configure min/max instances and concurrency |
| privileged/devices/capabilities | Block |

Run `scripts/compose_audit.py` to produce a first-pass report. The agent must still inspect application semantics.

## Reverse proxy migration

### Traefik using the Docker provider

A Traefik configuration that reads `/var/run/docker.sock`, discovers labels, listens on ports 80/443, and manages Let's Encrypt certificates is designed for a Docker host, not Cloud Run.

To retain Traefik:

- remove the Docker provider and socket mount;
- remove ACME and certificate storage;
- remove container-managed external TLS listeners and redirects;
- listen on the Cloud Run ingress port;
- define routes and upstreams with static or file-based configuration;
- route to sidecars through localhost or container names;
- write access logs to stdout;
- keep the dashboard disabled or private.

For a simple frontend plus API, using the frontend's existing Nginx container as ingress is often smaller and easier to operate than retaining a separate proxy sidecar.

### Rate limiting and security headers

Reverse-proxy rate limits inside one Cloud Run instance are per-instance, not necessarily global. Scaling can multiply the effective limit. Document that behavior and use an external, shared enforcement layer when globally consistent limits are required; provisioning such a layer is outside this skill.

Cloud Run terminates TLS, but the application or ingress proxy can still add HTTP security headers. Validate forwarded headers and trusted proxy behavior rather than copying Docker-host assumptions.

## Recommended conversion process

1. Identify each service's purpose, port, state, startup dependency, runtime identity, and scaling need.
2. Reject durable database or Docker-host dependencies.
3. Decide whether the containers truly belong in one Cloud Run service.
4. Choose exactly one ingress container.
5. Replace dynamic Docker routing with explicit routes.
6. Remove TLS/ACME and host-network assumptions.
7. Assign unique internal ports and update application URLs.
8. Convert health checks to probes.
9. Replace plaintext environment secrets with references to existing secrets.
10. Build and publish images outside this skill.
11. Generate the Cloud Run service YAML with immutable image references.
12. Dry-run, deploy as a zero-traffic candidate, verify, and request traffic approval.
