#!/usr/bin/env python3
"""Audit a Docker Compose file for Cloud Run multi-container compatibility.

The audit is intentionally conservative. It identifies Docker-host assumptions,
stateful storage, multiple ingress candidates, secret handling, and constructs
that require deliberate translation. It does not prove that an application is
Cloud Run compatible.

Exit codes:
  0  no blockers detected
  2  one or more blockers detected
  3  file or parser error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SEVERITY_ORDER = {"BLOCKER": 0, "ADAPT": 1, "REVIEW": 2, "INFO": 3}
SECRET_KEY_RE = re.compile(r"(?:PASSWORD|PASSWD|SECRET|API[_-]?KEY|PRIVATE[_-]?KEY|CREDENTIAL)", re.I)
TOKEN_METADATA_RE = re.compile(r"(?:EXPIRE|EXPIRY|TTL|LIFETIME|DURATION|MINUTES|SECONDS|ALGORITHM)", re.I)
STATEFUL_IMAGE_RE = re.compile(r"(?:^|/)(postgres|mysql|mariadb|mongo(?:db)?|redis|couchdb|elasticsearch|opensearch)(?::|@|$)", re.I)
STATEFUL_TARGET_RE = re.compile(
    r"^/(?:var/lib/postgresql/data|var/lib/mysql|var/lib/mongodb|data/db|usr/share/elasticsearch/data|data)(?:/|$)",
    re.I,
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    action: str
    service: str | None = None


class Audit:
    def __init__(self, source: Path, loader: str) -> None:
        self.source = source
        self.loader = loader
        self.issues: list[Issue] = []
        self.ingress_candidates: list[str] = []
        self.service_count = 0

    def add(self, severity: str, code: str, message: str, action: str, service: str | None = None) -> None:
        issue = Issue(severity, code, message, action, service)
        if issue not in self.issues:
            self.issues.append(issue)

    @property
    def blockers(self) -> int:
        return sum(issue.severity == "BLOCKER" for issue in self.issues)

    def sorted_issues(self) -> list[Issue]:
        return sorted(
            self.issues,
            key=lambda item: (SEVERITY_ORDER[item.severity], item.service or "", item.code, item.message),
        )


def executable(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def load_compose(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            return None, "pyyaml", "Compose root must be a YAML mapping."
        return data, "pyyaml", None
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        return None, "pyyaml", f"Unable to parse Compose YAML: {exc}"

    ruby = executable("ruby")
    if ruby:
        program = (
            "require 'yaml'; require 'json'; "
            "obj = YAML.safe_load(File.read(ARGV[0]), permitted_classes: [], aliases: true); "
            "STDOUT.write(JSON.generate(obj))"
        )
        completed = subprocess.run(
            [ruby, "-e", program, str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            try:
                data = json.loads(completed.stdout)
                if isinstance(data, dict):
                    return data, "ruby-yaml", None
                return None, "ruby-yaml", "Compose root must be a YAML mapping."
            except json.JSONDecodeError as exc:
                return None, "ruby-yaml", f"Ruby returned invalid JSON: {exc}"

    docker = executable("docker")
    if docker:
        completed = subprocess.run(
            [docker, "compose", "-f", str(path), "config", "--format", "json"],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            try:
                data = json.loads(completed.stdout)
                if isinstance(data, dict):
                    return data, "docker-compose-json", None
            except json.JSONDecodeError as exc:
                return None, "docker-compose-json", f"Docker Compose returned invalid JSON: {exc}"
        return None, "docker-compose-json", completed.stderr.strip() or "docker compose config failed"

    return None, "none", "No YAML parser is available. Install PyYAML, Ruby, or Docker Compose."


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key}={flatten_text(item)}" for key, item in value.items())
    return str(value)


def labels_as_pairs(value: Any) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            pairs.append((str(key), "" if item is None else str(item)))
    elif isinstance(value, list):
        for item in value:
            text = str(item)
            if "=" in text:
                key, val = text.split("=", 1)
            else:
                key, val = text, ""
            pairs.append((key, val))
    return pairs


def is_sensitive_key(key: str) -> bool:
    if SECRET_KEY_RE.search(key):
        return True
    return bool(re.search(r"(?:^|[_-])TOKEN(?:$|[_-])", key, re.I)) and not bool(TOKEN_METADATA_RE.search(key))


def environment_as_pairs(value: Any) -> list[tuple[str, str | None]]:
    pairs: list[tuple[str, str | None]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            pairs.append((str(key), None if item is None else str(item)))
    elif isinstance(value, list):
        for item in value:
            text = str(item)
            if "=" in text:
                key, val = text.split("=", 1)
                pairs.append((key, val))
            else:
                pairs.append((text, None))
    return pairs


def parse_short_mount(text: str) -> tuple[str | None, str | None, str]:
    # Compose short syntax is source:target[:mode]. Container-only anonymous
    # volumes can contain only the target path.
    parts = text.split(":")
    if len(parts) == 1:
        return None, parts[0], "volume"
    if len(parts) >= 2:
        source = parts[0]
        target = parts[1]
        mount_type = "bind" if source.startswith(("/", ".", "~")) else "volume"
        return source, target, mount_type
    return None, None, "unknown"


def parse_mount(value: Any) -> tuple[str | None, str | None, str]:
    if isinstance(value, str):
        return parse_short_mount(value)
    if isinstance(value, dict):
        source = value.get("source")
        target = value.get("target")
        mount_type = value.get("type", "volume")
        return (
            str(source) if source is not None else None,
            str(target) if target is not None else None,
            str(mount_type),
        )
    return None, None, "unknown"


def has_cloudrun_ingress_extension(service: dict[str, Any]) -> bool:
    extension = service.get("x-google-cloudrun")
    if isinstance(extension, dict):
        value = extension.get("ingress-container")
        return value is True or str(value).lower() == "true"
    return False


def port_entries(value: Any) -> list[str]:
    result: list[str] = []
    for item in listify(value):
        if isinstance(item, dict):
            published = item.get("published")
            target = item.get("target")
            result.append(f"{published}:{target}" if published is not None else str(target))
        else:
            result.append(str(item))
    return result


def audit_service(name: str, service: dict[str, Any], audit: Audit, top_volumes: set[str]) -> None:
    image = str(service.get("image") or "")
    command_text = " ".join(
        part for part in [flatten_text(service.get("entrypoint")), flatten_text(service.get("command"))] if part
    )
    combined = f"{image} {command_text}".lower()

    if service.get("build") is not None:
        audit.add(
            "REVIEW",
            "BUILD_OUT_OF_SCOPE",
            "The service uses a Compose build definition.",
            "Build and publish an immutable image outside this Cloud Run skill, then replace build with an image digest.",
            name,
        )
    if image and not any(marker in image for marker in ("/", ".pkg.dev", ".gcr.io", "@sha256:")):
        audit.add(
            "REVIEW",
            "LOCAL_IMAGE_REFERENCE",
            f"Image reference '{image}' may be local or ambiguous.",
            "Use a registry image accessible to Cloud Run, preferably by digest.",
            name,
        )
    if image and "@sha256:" not in image:
        audit.add(
            "INFO",
            "MUTABLE_IMAGE_TAG",
            f"Image '{image}' is not pinned by digest.",
            "Resolve and deploy an immutable digest for reproducibility.",
            name,
        )

    ports = port_entries(service.get("ports"))
    explicit_ingress = has_cloudrun_ingress_extension(service)
    if ports or explicit_ingress:
        audit.ingress_candidates.append(name)
    if len(ports) > 1:
        audit.add(
            "ADAPT",
            "MULTIPLE_PUBLISHED_PORTS",
            f"Published ports {ports} do not map directly to Cloud Run's single ingress container port.",
            "Choose one ingress port and keep all other ports internal to sidecars.",
            name,
        )
    if any(re.search(r"(?:^|:)80(?::|$)", port) or re.search(r"(?:^|:)443(?::|$)", port) for port in ports):
        audit.add(
            "ADAPT",
            "HOST_TLS_PORTS",
            f"Published ports {ports} include Docker-host HTTP/TLS ports.",
            "Let Cloud Run terminate external TLS and configure one ingress container port, normally 8080.",
            name,
        )

    if service.get("restart") is not None:
        audit.add(
            "ADAPT",
            "RESTART_POLICY",
            f"restart: {service.get('restart')} is a Docker-host lifecycle policy.",
            "Remove it; Cloud Run manages instance lifecycle and restarts.",
            name,
        )

    if service.get("container_name") is not None:
        audit.add(
            "INFO",
            "CONTAINER_NAME",
            "container_name is not a production identity or lifecycle control in Cloud Run.",
            "Use the Cloud Run container name only for configuration clarity and dependency references.",
            name,
        )

    if service.get("network_mode") == "host":
        audit.add(
            "BLOCKER",
            "HOST_NETWORK",
            "Host networking is incompatible with the Cloud Run sandbox model.",
            "Remove host networking and use the shared instance network with localhost or container names.",
            name,
        )
    elif service.get("network_mode") is not None:
        audit.add(
            "ADAPT",
            "NETWORK_MODE",
            f"network_mode: {service.get('network_mode')} requires review.",
            "Use Cloud Run's shared network namespace; do not depend on Docker network modes.",
            name,
        )

    if service.get("networks") is not None:
        audit.add(
            "INFO",
            "COMPOSE_NETWORKS",
            "Compose network membership does not create isolation between containers in one Cloud Run instance.",
            "Remove Docker bridge assumptions and use explicit internal ports.",
            name,
        )

    for field in ("privileged", "devices", "cap_add", "cap_drop", "pid", "ipc"):
        value = service.get(field)
        if value not in (None, False, [], {}):
            audit.add(
                "BLOCKER",
                "HOST_PRIVILEGE",
                f"The service uses unsupported or unsafe host-level setting '{field}'.",
                "Remove the host-level capability or redesign the component for Cloud Run.",
                name,
            )

    depends_on = service.get("depends_on")
    if depends_on is not None:
        has_condition = isinstance(depends_on, dict) and any(
            isinstance(item, dict) and item.get("condition") for item in depends_on.values()
        )
        audit.add(
            "ADAPT",
            "STARTUP_DEPENDENCY",
            "Compose depends_on requires deliberate Cloud Run startup dependency and probe configuration."
            + (" It includes condition semantics." if has_condition else ""),
            "Configure startup probes on dependencies and explicit container startup order; verify readiness semantics.",
            name,
        )

    if service.get("healthcheck") is not None:
        audit.add(
            "ADAPT",
            "HEALTHCHECK_TRANSLATION",
            "Compose healthcheck is not a one-to-one Cloud Run health policy.",
            "Map it to startup/liveness/readiness probes and an external post-deployment smoke test.",
            name,
        )

    labels = labels_as_pairs(service.get("labels"))
    traefik_labels = [key for key, _value in labels if key.lower().startswith("traefik.")]
    if traefik_labels:
        audit.add(
            "ADAPT",
            "TRAEFIK_DOCKER_LABELS",
            f"Found {len(traefik_labels)} Traefik Docker label(s).",
            "Replace Docker-provider discovery with explicit static/file routing to internal sidecar ports.",
            name,
        )
    elif labels:
        audit.add(
            "REVIEW",
            "COMPOSE_LABELS",
            "Compose labels may not affect Cloud Run runtime behavior.",
            "Verify every label against Cloud Run's supported Compose subset or move intent into service YAML.",
            name,
        )

    if "--providers.docker" in combined or "providers.docker" in combined:
        audit.add(
            "BLOCKER",
            "DOCKER_PROVIDER",
            "The container expects Docker daemon service discovery.",
            "Remove the Docker provider and define routes explicitly; Cloud Run does not expose a Docker daemon.",
            name,
        )
    if "certificatesresolvers" in combined or "acme." in combined or "letsencrypt" in combined:
        audit.add(
            "ADAPT",
            "CONTAINER_ACME",
            "The container manages ACME certificates or Let's Encrypt state.",
            "Remove ACME/TLS certificate management and use Cloud Run's external HTTPS termination.",
            name,
        )
    if "accesslog.filepath" in combined or re.search(r"/var/log/", combined):
        audit.add(
            "ADAPT",
            "FILE_LOGGING",
            "Operational logs are configured for a container filesystem path.",
            "Write structured logs to stdout/stderr for Cloud Logging.",
            name,
        )

    stateful_image = bool(STATEFUL_IMAGE_RE.search(image))
    for mount in listify(service.get("volumes")):
        source, target, mount_type = parse_mount(mount)
        source_text = source or "<anonymous>"
        target_text = target or "<unknown>"
        if source and source.rstrip("/") == "/var/run/docker.sock":
            audit.add(
                "BLOCKER",
                "DOCKER_SOCKET",
                "The service mounts /var/run/docker.sock.",
                "Remove Docker socket access; Cloud Run does not provide a host Docker daemon.",
                name,
            )
        elif source and source.startswith(("/", ".", "~")):
            audit.add(
                "ADAPT",
                "HOST_BIND_MOUNT",
                f"Bind mount '{source_text}:{target_text}' depends on local host files.",
                "Bake static files into the image or use an explicitly approved Cloud Run volume/secret reference.",
                name,
            )
        elif source and source in top_volumes:
            audit.add(
                "REVIEW",
                "NAMED_VOLUME",
                f"Named volume '{source_text}' is mounted at '{target_text}'.",
                "Classify the data as ephemeral, shared temporary, configuration, or durable before choosing a Cloud Run storage mapping.",
                name,
            )
        elif mount_type not in {"volume", "bind", "tmpfs"}:
            audit.add(
                "REVIEW",
                "VOLUME_TYPE",
                f"Volume type '{mount_type}' requires Cloud Run support review.",
                "Use only a Cloud Run-supported volume type and preserve security semantics.",
                name,
            )

        if stateful_image and target and STATEFUL_TARGET_RE.search(target):
            audit.add(
                "BLOCKER",
                "STATEFUL_DATABASE_VOLUME",
                f"Stateful image '{image}' stores durable data at '{target}'.",
                "Move the database to an external managed prerequisite; do not run its durable data directory on Cloud Run instance storage or generic object storage.",
                name,
            )
        if target and target.startswith("/var/log"):
            audit.add(
                "ADAPT",
                "LOG_VOLUME",
                f"Log path '{target}' is mounted as a volume.",
                "Send operational logs to stdout/stderr instead of persisting local log files.",
                name,
            )

    if stateful_image:
        audit.add(
            "REVIEW",
            "STATEFUL_SERVICE",
            f"Image '{image}' appears to be a stateful data service.",
            "Confirm that it is not being used as a durable production database inside Cloud Run.",
            name,
        )

    for key, value in environment_as_pairs(service.get("environment")):
        if is_sensitive_key(key):
            if value is None or value == "" or re.fullmatch(r"\$\{[^}]+\}", value.strip()):
                audit.add(
                    "ADAPT",
                    "SECRET_ENV_REFERENCE",
                    f"Sensitive variable '{key}' is sourced from the Compose environment.",
                    "Reference an existing Secret Manager secret; do not copy the resolved value into service YAML or command history.",
                    name,
                )
            else:
                audit.add(
                    "BLOCKER",
                    "PLAINTEXT_SECRET",
                    f"Sensitive variable '{key}' appears to contain a literal value.",
                    "Remove the value from Compose and use an existing Secret Manager reference.",
                    name,
                )
        if key.upper() == "DATABASE_URL" and value and re.search(r"@[A-Za-z0-9_-]+:\d+", value):
            audit.add(
                "REVIEW",
                "COMPOSE_DATABASE_HOST",
                "DATABASE_URL appears to target another Compose service by hostname.",
                "Replace it with the approved external database connection method or a deliberately co-located non-durable dependency.",
                name,
            )

    if service.get("secrets") is not None:
        audit.add(
            "ADAPT",
            "COMPOSE_SECRETS",
            "The service consumes Compose secrets.",
            "Map them to references to existing Secret Manager secrets and verify runtime service-account access.",
            name,
        )


def audit_compose(data: dict[str, Any], source: Path, loader: str) -> Audit:
    audit = Audit(source, loader)
    services = data.get("services")
    if not isinstance(services, dict) or not services:
        audit.add("BLOCKER", "NO_SERVICES", "No Compose services mapping was found.", "Provide a valid Compose file with services.")
        return audit

    audit.service_count = len(services)
    if audit.service_count > 10:
        audit.add(
            "BLOCKER",
            "CONTAINER_LIMIT",
            f"The Compose file defines {audit.service_count} services; one Cloud Run instance supports at most ten containers.",
            "Split the architecture deliberately or remove non-runtime services.",
        )

    top_volumes_value = data.get("volumes")
    top_volumes = set(str(key) for key in top_volumes_value.keys()) if isinstance(top_volumes_value, dict) else set()

    for name, raw_service in services.items():
        if not isinstance(raw_service, dict):
            audit.add("BLOCKER", "INVALID_SERVICE", "Service definition is not a mapping.", "Fix the Compose syntax.", str(name))
            continue
        audit_service(str(name), raw_service, audit, top_volumes)

    unique_ingress = sorted(set(audit.ingress_candidates))
    audit.ingress_candidates = unique_ingress
    if len(unique_ingress) == 0:
        audit.add(
            "REVIEW",
            "NO_INGRESS_CANDIDATE",
            "No service publishes a port or declares the Cloud Run ingress-container extension.",
            "Choose exactly one ingress container and configure its Cloud Run container port.",
        )
    elif len(unique_ingress) > 1:
        audit.add(
            "BLOCKER",
            "MULTIPLE_INGRESS_CANDIDATES",
            "Multiple services appear to be ingress candidates: " + ", ".join(unique_ingress) + ".",
            "Choose exactly one ingress container and keep every other container internal.",
        )

    networks = data.get("networks")
    if isinstance(networks, dict):
        for name, config in networks.items():
            driver = config.get("driver") if isinstance(config, dict) else None
            if driver == "bridge":
                audit.add(
                    "INFO",
                    "BRIDGE_NETWORK",
                    f"Top-level network '{name}' uses the Docker bridge driver.",
                    "Remove the bridge network from the Cloud Run design; containers share an instance network.",
                )
            elif driver:
                audit.add(
                    "REVIEW",
                    "CUSTOM_NETWORK_DRIVER",
                    f"Top-level network '{name}' uses driver '{driver}'.",
                    "Redesign networking with Cloud Run ingress and approved VPC attachment semantics.",
                )

    secrets = data.get("secrets")
    if isinstance(secrets, dict):
        for name, config in secrets.items():
            if isinstance(config, dict) and config.get("file"):
                audit.add(
                    "ADAPT",
                    "SECRET_FILE_PROVISIONING",
                    f"Top-level secret '{name}' is sourced from a local file.",
                    "Do not let production Compose auto-provision it; reference an existing Secret Manager secret outside this skill's creation scope.",
                )

    if top_volumes:
        audit.add(
            "REVIEW",
            "TOP_LEVEL_VOLUMES",
            "Top-level named volumes are present: " + ", ".join(sorted(top_volumes)) + ".",
            "Review each for durable-state assumptions before generating Cloud Run YAML.",
        )

    return audit


def render_markdown(audit: Audit) -> str:
    issues = audit.sorted_issues()
    counts = {severity: sum(item.severity == severity for item in issues) for severity in SEVERITY_ORDER}
    recommendation = (
        "Do not deploy this Compose file unchanged. Resolve all blockers and generate a reviewed Cloud Run service YAML."
        if counts["BLOCKER"]
        else "No static blocker was detected, but adapt/review findings still require a reviewed Cloud Run service YAML and gcloud dry-run."
    )

    lines = [
        "# Cloud Run Compose compatibility audit",
        "",
        f"- Source: `{audit.source}`",
        f"- Parser: `{audit.loader}`",
        f"- Services: {audit.service_count}",
        f"- Ingress candidates: {', '.join(audit.ingress_candidates) if audit.ingress_candidates else 'none'}",
        f"- Findings: {counts['BLOCKER']} blocker, {counts['ADAPT']} adapt, {counts['REVIEW']} review, {counts['INFO']} info",
        "",
        f"**Recommendation:** {recommendation}",
        "",
    ]

    for severity in ("BLOCKER", "ADAPT", "REVIEW", "INFO"):
        group = [issue for issue in issues if issue.severity == severity]
        if not group:
            continue
        lines.extend([f"## {severity}", ""])
        for issue in group:
            scope = f" `{issue.service}`" if issue.service else ""
            lines.append(f"- **{issue.code}**{scope}: {issue.message} **Action:** {issue.action}")
        lines.append("")

    lines.extend(
        [
            "## Next controlled step",
            "",
            "Run the Cloud Run Compose CLI dry-run only after reviewing this report, then convert the desired state to a Cloud Run service YAML. A successful static audit is not deployment approval.",
        ]
    )
    return "\n".join(lines)


def render_json(audit: Audit) -> str:
    issues = audit.sorted_issues()
    payload = {
        "source": str(audit.source),
        "loader": audit.loader,
        "service_count": audit.service_count,
        "ingress_candidates": audit.ingress_candidates,
        "summary": {
            severity.lower(): sum(item.severity == severity for item in issues)
            for severity in ("BLOCKER", "ADAPT", "REVIEW", "INFO")
        },
        "deploy_unchanged": False if audit.blockers else None,
        "issues": [asdict(issue) for issue in issues],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compose_file", help="Path to compose.yaml or docker-compose.yml")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    path = Path(args.compose_file)
    if not path.is_file():
        print(f"Compose file not found: {path}", file=sys.stderr)
        return 3

    data, loader, error = load_compose(path)
    if error or data is None:
        print(error or "Unable to load Compose file.", file=sys.stderr)
        return 3

    audit = audit_compose(data, path, loader)
    print(render_markdown(audit) if args.format == "markdown" else render_json(audit))
    return 2 if audit.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
