#!/usr/bin/env python3
"""Classify a single gcloud Cloud Run command under the skill approval policy.

This is a guardrail, not a complete policy engine. It checks the exact command for
high-risk intent, explicit project/region context, and—when replacing a service—
whether a supplied manifest pins traffic to explicit revisions.

Exit codes:
  0  ALLOW_AUTONOMOUS
  10 REQUIRE_CONFIRMATION
  20 BLOCKED
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ALLOW = "ALLOW_AUTONOMOUS"
CONFIRM = "REQUIRE_CONFIRMATION"
BLOCKED = "BLOCKED"


@dataclass
class Result:
    classification: str = ALLOW
    approval_categories: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed_path: str = ""
    release_track: str = "ga"

    def add_confirmation(self, category: str, reason: str) -> None:
        if self.classification != BLOCKED:
            self.classification = CONFIRM
        if category not in self.approval_categories:
            self.approval_categories.append(category)
        if reason not in self.reasons:
            self.reasons.append(reason)

    def block(self, reason: str) -> None:
        self.classification = BLOCKED
        if reason not in self.reasons:
            self.reasons.append(reason)

    def require(self, requirement: str) -> None:
        if requirement not in self.requirements:
            self.requirements.append(requirement)

    def warn(self, warning: str) -> None:
        if warning not in self.warnings:
            self.warnings.append(warning)


SHELL_CONTROL = {";", "&&", "||", "|", "&", ">", ">>", "<", "<<"}
PUBLIC_MEMBERS = {"allusers", "allauthenticatedusers"}

# Flags that can remove or replace significant runtime configuration.
DESTRUCTIVE_FLAG_PREFIXES = (
    "--clear-env-vars",
    "--clear-secrets",
    "--clear-volumes",
    "--clear-volume-mounts",
    "--clear-cloudsql-instances",
    "--clear-vpc-connector",
    "--clear-network",
    "--clear-service-account",
    "--remove-containers",
    "--remove-secrets",
    "--remove-volume",
    "--remove-volume-mount",
    "--remove-cloudsql-instances",
    "--set-env-vars",
    "--set-secrets",
    "--set-cloudsql-instances",
)

READ_ONLY_PATHS = {
    ("services", "list"),
    ("services", "describe"),
    ("services", "get-iam-policy"),
    ("services", "proxy"),
    ("services", "logs", "read"),
    ("revisions", "list"),
    ("revisions", "describe"),
    ("regions", "list"),
}


def normalize_flag_tokens(tokens: list[str]) -> list[str]:
    """Normalize '--flag value' to '--flag=value' for selected policy checks."""
    normalized: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.startswith("--") and "=" not in token and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if not next_token.startswith("-"):
                normalized.append(f"{token}={next_token}")
                i += 2
                continue
        normalized.append(token)
        i += 1
    return normalized


def has_flag(tokens: Iterable[str], name: str) -> bool:
    return any(token == name or token.startswith(name + "=") for token in tokens)


def flag_value(tokens: Iterable[str], name: str) -> str | None:
    prefix = name + "="
    for token in tokens:
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def parse_gcloud_path(tokens: list[str], result: Result) -> tuple[list[str], list[str]] | None:
    if not tokens or tokens[0] != "gcloud":
        result.block("The command must be one direct gcloud invocation.")
        return None

    if any(token in SHELL_CONTROL for token in tokens):
        result.block("Shell control operators are not allowed in a guarded mutation command.")
        return None
    if any("\n" in token or "\r" in token for token in tokens):
        result.block("Multi-line command payloads are not allowed.")
        return None
    if any("$(" in token or "`" in token for token in tokens):
        result.block("Command substitution is not allowed in a guarded mutation command.")
        return None

    idx = 1
    if idx < len(tokens) and tokens[idx] in {"alpha", "beta"}:
        result.release_track = tokens[idx]
        idx += 1

    if idx >= len(tokens) or tokens[idx] != "run":
        result.block("This skill guard accepts only gcloud run commands.")
        return None
    idx += 1

    # Collect command path until a flag or likely positional argument. Known
    # command group shapes are handled explicitly.
    remaining = tokens[idx:]
    if not remaining:
        result.block("Missing Cloud Run command group or command.")
        return None

    path: list[str] = []
    if remaining[0] == "deploy":
        path = ["deploy"]
    elif remaining[0] == "compose":
        path = remaining[:2] if len(remaining) >= 2 else ["compose"]
    elif remaining[0] == "services":
        if len(remaining) >= 3 and remaining[1] == "logs":
            path = remaining[:3]
        elif len(remaining) >= 2:
            path = remaining[:2]
        else:
            path = ["services"]
    elif remaining[0] == "revisions":
        path = remaining[:2] if len(remaining) >= 2 else ["revisions"]
    elif remaining[0] == "regions":
        path = remaining[:2] if len(remaining) >= 2 else ["regions"]
    elif remaining[0] in {"jobs", "worker-pools", "multi-region-services", "domain-mappings"}:
        result.block(f"gcloud run {remaining[0]} is outside this skill's service scope.")
        return None
    else:
        result.block(f"Unsupported Cloud Run command path: {' '.join(remaining[:3])}")
        return None

    result.parsed_path = "gcloud " + (result.release_track + " " if result.release_track != "ga" else "") + "run " + " ".join(path)
    return path, remaining


def load_yaml_document(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            return None, "Manifest root must be a YAML mapping."
        return data, None
    except ModuleNotFoundError:
        pass
    except Exception as exc:  # pragma: no cover - parser-specific details
        return None, f"Unable to parse manifest with PyYAML: {exc}"

    # Fallback to Ruby's standard YAML library when available. This avoids a
    # hard Python dependency while keeping the script deterministic.
    ruby = shutil_which("ruby")
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
                    return data, None
                return None, "Manifest root must be a YAML mapping."
            except json.JSONDecodeError as exc:
                return None, f"Ruby parsed YAML but returned invalid JSON: {exc}"
        return None, f"Unable to parse manifest with Ruby YAML: {completed.stderr.strip()}"

    return None, "No YAML parser is available. Install PyYAML or provide Ruby."


def shutil_which(command: str) -> str | None:
    path = os.environ.get("PATH", "")
    for directory in path.split(os.pathsep):
        candidate = Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def inspect_replace_manifest(path: Path, result: Result) -> None:
    if not path.is_file():
        result.block(f"Manifest not found: {path}")
        return

    data, error = load_yaml_document(path)
    if error:
        result.block(error)
        return
    assert data is not None

    if data.get("kind") != "Service":
        result.block("Manifest kind must be Service.")
        return
    if data.get("apiVersion") != "serving.knative.dev/v1":
        result.warn("Expected apiVersion serving.knative.dev/v1; verify the installed CLI supports the supplied version.")

    spec = data.get("spec")
    if not isinstance(spec, dict):
        result.block("Manifest is missing spec.")
        return

    traffic = spec.get("traffic")
    if not isinstance(traffic, list) or not traffic:
        result.add_confirmation(
            "production_traffic",
            "The replacement manifest does not pin an explicit traffic map; a new revision could receive traffic.",
        )
        return

    template = spec.get("template")
    candidate_name: str | None = None
    if isinstance(template, dict):
        metadata = template.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("name"), str):
            candidate_name = metadata["name"]

    total = 0
    for index, target in enumerate(traffic):
        if not isinstance(target, dict):
            result.block(f"spec.traffic[{index}] must be a mapping.")
            return
        if target.get("latestRevision") is True:
            result.add_confirmation(
                "production_traffic",
                f"spec.traffic[{index}] follows latestRevision and can move traffic to the candidate.",
            )
        revision_name = target.get("revisionName")
        if not isinstance(revision_name, str) or not revision_name:
            result.add_confirmation(
                "production_traffic",
                f"spec.traffic[{index}] is not pinned to an explicit revisionName.",
            )
        percent = target.get("percent", 0)
        if isinstance(percent, bool) or not isinstance(percent, int) or percent < 0 or percent > 100:
            result.block(f"spec.traffic[{index}].percent must be an integer from 0 to 100.")
            return
        total += percent
        if candidate_name and revision_name == candidate_name and percent > 0:
            result.add_confirmation(
                "production_traffic",
                f"Candidate revision {candidate_name} is assigned {percent}% production traffic.",
            )

    if total != 100:
        result.block(f"Traffic percentages total {total}; expected exactly 100.")

    if candidate_name is None:
        result.warn("The manifest does not name the candidate revision deterministically.")

    result.require("A successful gcloud run services replace --dry-run for this exact manifest.")
    result.require("A semantic diff proving no unrequested destructive removals.")
    result.require("A current service and IAM snapshot.")


def detect_public_access(tokens: list[str], result: Result) -> None:
    lowered = [token.lower() for token in tokens]
    if has_flag(lowered, "--allow-unauthenticated") or has_flag(lowered, "--no-invoker-iam-check"):
        result.add_confirmation("public_access", "The command enables unauthenticated invocation.")

    member = flag_value(lowered, "--member")
    if member:
        principal = member.split(":", 1)[-1]
        if principal in PUBLIC_MEMBERS:
            result.add_confirmation("public_access", f"The IAM member {member} widens invocation to a public principal.")

    ingress = flag_value(lowered, "--ingress")
    if ingress == "all":
        result.add_confirmation("public_access", "The command sets ingress to all sources and widens external exposure.")
    elif ingress in {"internal", "internal-and-cloud-load-balancing"}:
        result.add_confirmation("destructive", "Changing ingress restrictions can interrupt currently serving callers.")


def detect_destructive_flags(tokens: list[str], result: Result) -> None:
    lowered = [token.lower() for token in tokens]
    for token in lowered:
        if any(token == prefix or token.startswith(prefix + "=") for prefix in DESTRUCTIVE_FLAG_PREFIXES):
            result.add_confirmation("destructive", f"The flag {token.split('=', 1)[0]} can remove or replace existing configuration.")

    if has_flag(lowered, "--no-allow-unauthenticated") or has_flag(lowered, "--invoker-iam-check"):
        result.add_confirmation("destructive", "The command can revoke existing unauthenticated access and interrupt callers.")

    scaling = flag_value(lowered, "--scaling")
    if scaling == "0":
        result.add_confirmation("destructive", "Setting scaling to zero disables the service.")


def ensure_context(tokens: list[str], path: list[str], result: Result, mutation: bool) -> None:
    normalized = normalize_flag_tokens(tokens)
    project = flag_value(normalized, "--project")
    region = flag_value(normalized, "--region")

    if not project:
        if mutation:
            result.block("Mutating Cloud Run commands require an explicit --project.")
        else:
            result.warn("Use an explicit --project for deterministic inspection.")

    region_not_applicable = tuple(path) == ("regions", "list")
    if not region and not region_not_applicable:
        if mutation:
            result.block("Mutating Cloud Run commands require an explicit --region.")
        else:
            result.warn("Use an explicit --region for deterministic inspection.")


def classify(command: str, manifest: str | None) -> Result:
    result = Result()
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        result.block(f"Unable to parse command: {exc}")
        return result

    parsed = parse_gcloud_path(tokens, result)
    if parsed is None:
        return result
    path, _remaining = parsed
    normalized = normalize_flag_tokens(tokens)
    path_tuple = tuple(path)

    if path_tuple in READ_ONLY_PATHS:
        ensure_context(normalized, path, result, mutation=False)
        result.require("Keep the operation read-only; do not chain a mutation.")
        return result

    mutation = True
    ensure_context(normalized, path, result, mutation=mutation)
    detect_public_access(normalized, result)
    detect_destructive_flags(normalized, result)

    if result.release_track in {"alpha", "beta"}:
        result.warn(f"The command uses the {result.release_track} release track; verify current local help and production acceptance.")

    if path_tuple == ("deploy",):
        if has_flag(normalized, "--source"):
            result.block("Source deployment invokes build infrastructure and is outside this skill's scope; provide a prebuilt image.")
        if not has_flag(normalized, "--image") and not has_flag(normalized, "--function"):
            result.block("Deploy requires an explicit prebuilt --image in this skill.")
        if has_flag(normalized, "--function"):
            result.block("Cloud Run functions are outside this skill's service scope.")
        if not has_flag(normalized, "--no-traffic"):
            result.add_confirmation("production_traffic", "Deploy without --no-traffic can send service traffic to the new revision.")
        result.require("A successful dry-run of an equivalent service manifest.")
        result.require("A current service and IAM snapshot for an existing service.")
        result.require("Post-deployment revision readiness and log verification.")

    elif path_tuple == ("services", "replace"):
        if has_flag(normalized, "--dry-run"):
            result.require("Review the dry-run output and semantic manifest diff before applying.")
        else:
            if not manifest:
                result.block("Actual service replacement requires --manifest so traffic safety can be inspected.")
            else:
                inspect_replace_manifest(Path(manifest), result)

    elif path_tuple == ("services", "update-traffic"):
        result.add_confirmation("production_traffic", "Every update-traffic operation changes production routing.")

    elif path_tuple in {("services", "delete"), ("revisions", "delete")}:
        result.add_confirmation("destructive", "The command deletes a Cloud Run resource.")

    elif path_tuple == ("services", "set-iam-policy"):
        result.add_confirmation("destructive", "Replacing the full service IAM policy can remove unrelated bindings.")

    elif path_tuple == ("services", "remove-iam-policy-binding"):
        result.add_confirmation("destructive", "Removing an IAM binding can interrupt callers.")

    elif path_tuple == ("services", "add-iam-policy-binding"):
        result.require("A current service IAM snapshot and exact principal/role review.")

    elif path_tuple == ("services", "update"):
        result.add_confirmation(
            "production_traffic",
            "Direct services update creates a revision and can receive traffic when the service follows latestRevision; prefer a pinned YAML replacement.",
        )

    elif path_tuple == ("compose", "up"):
        if has_flag(normalized, "--dry-run"):
            result.require("Run the bundled static Compose audit and review pre-GA limitations.")
        else:
            result.add_confirmation("production_traffic", "Compose up can create a serving revision and shift service traffic.")
            result.block("Non-dry-run Compose deployment is not an autonomous production path for this skill; generate a service YAML instead.")

    else:
        result.block(f"Unsupported mutating command path: {' '.join(path)}")

    return result


def render_text(result: Result) -> str:
    lines = [result.classification, f"Path: {result.parsed_path or 'unparsed'}"]
    if result.approval_categories:
        lines.append("Approval: " + ", ".join(result.approval_categories))
    if result.reasons:
        lines.append("Reasons:")
        lines.extend(f"- {item}" for item in result.reasons)
    if result.requirements:
        lines.append("Required evidence:")
        lines.extend(f"- {item}" for item in result.requirements)
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in result.warnings)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True, help="One exact gcloud command to classify.")
    parser.add_argument("--manifest", help="Service YAML used by an actual services replace command.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    result = classify(args.command, args.manifest)
    payload = {
        "classification": result.classification,
        "approval_categories": result.approval_categories,
        "reasons": result.reasons,
        "requirements": result.requirements,
        "warnings": result.warnings,
        "parsed_path": result.parsed_path,
        "release_track": result.release_track,
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(result))

    if result.classification == ALLOW:
        return 0
    if result.classification == CONFIRM:
        return 10
    return 20


if __name__ == "__main__":
    raise SystemExit(main())
