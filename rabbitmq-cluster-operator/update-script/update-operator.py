#!/usr/bin/env python3
"""
Update the RabbitMQ Cluster Operator Helm chart to a new upstream version.

Usage:
    python update-script/update-operator.py v2.19.1

Downloads the official cluster-operator.yml, splits all documents,
templatizes them for Helm, and writes them to the chart.

After running, review changes with `git diff` before committing.
"""

import sys
import re
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

import yaml

RELEASE_URL = (
    "https://github.com/rabbitmq/cluster-operator/releases/download"
    "/{version}/cluster-operator.yml"
)

UPSTREAM_NAMESPACE = "rabbitmq-system"

# Template files that are not generated from upstream and should be preserved.
PRESERVED_TEMPLATES = {"_helpers.tpl", "NOTES.txt"}


# ---------------------------------------------------------------------------
# Download & split
# ---------------------------------------------------------------------------

def download_manifest(version: str) -> str:
    """Download the upstream cluster-operator.yml manifest."""
    url = RELEASE_URL.format(version=version)
    print(f"==> Downloading cluster-operator.yml for {version}...")
    try:
        with urlopen(url) as resp:
            return resp.read().decode()
    except URLError as e:
        print(f"ERROR: Failed to download manifest: {e}")
        print(f"  Check that version {version} exists at:")
        print(
            f"  https://github.com/rabbitmq/cluster-operator/releases/tag/{version}"
        )
        sys.exit(1)


def split_documents(raw_text: str) -> list[tuple[dict, str]]:
    """Split multi-document YAML into (parsed_doc, raw_text) pairs.

    Uses yaml.safe_load for identification but preserves the original
    raw text for each document to maintain upstream formatting.
    """
    raw_parts = re.split(r"^---$", raw_text, flags=re.MULTILINE)
    raw_parts = [p.strip() + "\n" for p in raw_parts if p.strip()]
    pairs = []
    for raw in raw_parts:
        parsed = yaml.safe_load(raw)
        if parsed is not None:
            pairs.append((parsed, raw))
    return pairs


# ---------------------------------------------------------------------------
# Common templatization (applied to all resources)
# ---------------------------------------------------------------------------

def templatize_namespace(text: str) -> str:
    """Replace hardcoded upstream namespace with Helm template directive."""
    return text.replace(
        f"namespace: {UPSTREAM_NAMESPACE}",
        "namespace: {{ .Release.Namespace }}",
    )


def templatize_labels(text: str) -> str:
    """Replace upstream standard labels block with Helm include.

    Dynamically computes nindent from the indentation found in the text.
    Extra labels (e.g. servicebinding.io/controller) are preserved.
    """
    def replace_fn(match):
        indent = match.group(1)
        content_indent = indent + "  "
        nindent = len(content_indent)
        return (
            f"{indent}labels:\n"
            f'{content_indent}{{{{- include "rabbitmq-cluster-operator.labels"'
            f" . | nindent {nindent} }}}}\n"
        )

    pattern = (
        r"( +)labels:\n"
        r"\1  app\.kubernetes\.io/component: rabbitmq-operator\n"
        r"\1  app\.kubernetes\.io/name: rabbitmq-cluster-operator\n"
        r"\1  app\.kubernetes\.io/part-of: rabbitmq\n"
    )
    return re.sub(pattern, replace_fn, text)


# ---------------------------------------------------------------------------
# Kind-specific templatization
# ---------------------------------------------------------------------------

def templatize_deployment(text: str) -> str:
    """Apply Deployment-specific Helm templatization.

    Replaces image, replicas, resources, securityContext with values
    references and adds podLabels, podAnnotations, scheduling blocks.
    """
    result = text

    # Replicas
    result = re.sub(
        r"replicas: \d+",
        "replicas: {{ .Values.replicas }}",
        result,
        count=1,
    )

    # Image
    result = re.sub(
        r"( +image: ).+",
        r'\g<1>"{{ .Values.image.repository }}:{{ .Values.image.tag }}"',
        result,
    )

    # ImagePullPolicy (insert after image line)
    result = re.sub(
        r"( +)(image: .+\n)",
        r"\g<1>\g<2>\g<1>imagePullPolicy: {{ .Values.image.pullPolicy }}\n",
        result,
        count=1,
    )

    # Resources block: replace content with toYaml
    result = re.sub(
        r"(( +)resources:\n)(?:\2  .+\n)+",
        lambda m: (
            f"{m.group(1)}"
            f"{m.group(2)}  {{{{- toYaml .Values.resources | nindent {len(m.group(2)) + 2} }}}}\n"
        ),
        result,
    )

    # SecurityContext block: replace content with toYaml
    result = re.sub(
        r"(( +)securityContext:\n)(?:\2  .+\n)+",
        lambda m: (
            f"{m.group(1)}"
            f"{m.group(2)}  {{{{- toYaml .Values.securityContext | nindent {len(m.group(2)) + 2} }}}}\n"
        ),
        result,
    )

    # Pod labels: add podLabels block after the pod template labels include
    pod_include = '{{- include "rabbitmq-cluster-operator.labels" . | nindent 8 }}'
    if pod_include in result:
        result = result.replace(
            pod_include + "\n",
            pod_include + "\n"
            "        {{- with .Values.podLabels }}\n"
            "        {{- toYaml . | nindent 8 }}\n"
            "        {{- end }}\n",
            1,
        )

    # Pod annotations: insert before pod template "    spec:"
    result = result.replace(
        "    spec:\n",
        "      {{- with .Values.podAnnotations }}\n"
        "      annotations:\n"
        "        {{- toYaml . | nindent 8 }}\n"
        "      {{- end }}\n"
        "    spec:\n",
        1,
    )

    # Scheduling blocks: insert after terminationGracePeriodSeconds
    result = re.sub(
        r"(      terminationGracePeriodSeconds: \d+\n)",
        r"\g<1>"
        "      {{- with .Values.nodeSelector }}\n"
        "      nodeSelector:\n"
        "        {{- toYaml . | nindent 8 }}\n"
        "      {{- end }}\n"
        "      {{- with .Values.affinity }}\n"
        "      affinity:\n"
        "        {{- toYaml . | nindent 8 }}\n"
        "      {{- end }}\n"
        "      {{- with .Values.tolerations }}\n"
        "      tolerations:\n"
        "        {{- toYaml . | nindent 8 }}\n"
        "      {{- end }}\n",
        result,
    )

    return result


def templatize_serviceaccount(text: str) -> str:
    """Add labels and annotations support to ServiceAccount."""
    result = text

    # Add labels block if the upstream SA doesn't have one
    if "labels:" not in result:
        result = result.replace(
            "metadata:\n",
            "metadata:\n"
            "  labels:\n"
            '    {{- include "rabbitmq-cluster-operator.labels" . | nindent 4 }}\n',
            1,
        )

    # Add annotations support after namespace line
    result = re.sub(
        r"(  namespace: .+\n)",
        r"\g<1>"
        "  {{- with .Values.serviceAccount.annotations }}\n"
        "  annotations:\n"
        "    {{- toYaml . | nindent 4 }}\n"
        "  {{- end }}\n",
        result,
        count=1,
    )

    return result


# ---------------------------------------------------------------------------
# Document processing pipeline
# ---------------------------------------------------------------------------

def kind_to_filename(kind: str) -> str:
    """Convert a Kubernetes Kind to a template filename."""
    return kind.lower() + ".yaml"


def clean_generated_templates(templates_dir: Path) -> None:
    """Remove previously generated template files, preserve manual ones."""
    if not templates_dir.exists():
        return
    for f in templates_dir.iterdir():
        if f.name not in PRESERVED_TEMPLATES:
            f.unlink()


def process_documents(
    raw_text: str, version: str, chart_dir: Path,
) -> dict | None:
    """Process all upstream documents and write chart files.

    Dispatches each document by kind:
    - Namespace       -> skipped (Helm manages this)
    - CRD             -> crds/ as-is
    - Deployment      -> templates/ with full Helm templatization
    - ServiceAccount  -> templates/ with labels + annotations
    - Everything else -> templates/ with namespace + labels

    Returns the parsed Deployment doc for the summary, or None.
    """
    pairs = split_documents(raw_text)

    clean_generated_templates(chart_dir / "templates")

    # Group processed templates by kind
    templates: dict[str, list[tuple[str, str]]] = {}
    deployment_doc = None

    for parsed, raw in pairs:
        kind = parsed.get("kind", "")
        name = parsed.get("metadata", {}).get("name", "unknown")

        if kind == "Namespace":
            print(f"    Skipping {kind}/{name} (Helm manages namespaces)")
            continue

        if kind == "CustomResourceDefinition":
            crd_path = chart_dir / "crds" / "rabbitmqclusters.yaml"
            crd_path.write_text(raw + "\n")
            print(f"    -> crds/rabbitmqclusters.yaml")
            continue

        # Save the parsed deployment before templatizing (for summary)
        if kind == "Deployment":
            deployment_doc = parsed

        # Common templatization
        content = templatize_namespace(raw)
        content = templatize_labels(content)

        # Kind-specific templatization
        if kind == "Deployment":
            content = templatize_deployment(content)
        elif kind == "ServiceAccount":
            content = templatize_serviceaccount(content)

        # Add header
        header = (
            f"## {kind}: {name}\n"
            f"## Source: upstream cluster-operator.yml ({version})"
        )
        content = f"{header}\n{content}"

        templates.setdefault(kind, []).append((name, content))

    # Write one template file per kind
    for kind, items in templates.items():
        filename = kind_to_filename(kind)
        output = chart_dir / "templates" / filename
        combined = "\n---\n".join(content for _, content in items)
        output.write_text(combined + "\n")
        print(f"    -> templates/{filename}")

    return deployment_doc


# ---------------------------------------------------------------------------
# Version updates
# ---------------------------------------------------------------------------

def update_chart_yaml(chart_dir: Path, version: str) -> None:
    """Update appVersion in Chart.yaml."""
    print(f"==> Updating Chart.yaml appVersion to {version}...")
    chart_file = chart_dir / "Chart.yaml"
    content = chart_file.read_text()
    content = re.sub(
        r"^appVersion:.*$",
        f'appVersion: "{version}"',
        content,
        flags=re.MULTILINE,
    )
    chart_file.write_text(content)


def update_values_yaml(chart_dir: Path, image_tag: str) -> None:
    """Update image tag in values.yaml."""
    print(f"==> Updating values.yaml image tag to {image_tag}...")
    values_file = chart_dir / "values.yaml"
    content = values_file.read_text()
    content = re.sub(
        r"^(  tag:).*$",
        rf'\1 "{image_tag}"',
        content,
        flags=re.MULTILINE,
    )
    values_file.write_text(content)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(deploy_doc: dict | None, chart_dir: Path) -> None:
    """Print upstream deployment details for review."""
    print("==> Deployment summary...")
    if deploy_doc is None:
        print("    WARNING: No Deployment found in manifest")
        return

    container = deploy_doc["spec"]["template"]["spec"]["containers"][0]
    image = container.get("image", "")
    resources = container.get("resources", {})

    print(f"    Upstream image: {image}")

    values_file = chart_dir / "values.yaml"
    values = yaml.safe_load(values_file.read_text())
    current_repo = values.get("image", {}).get("repository", "")
    upstream_repo = image.rsplit(":", 1)[0] if ":" in image else image

    if current_repo != upstream_repo:
        print()
        print(
            f"    WARNING: Image repository changed:"
            f" '{current_repo}' -> '{upstream_repo}'"
        )
        print("             Update image.repository in values.yaml")

    limits = resources.get("limits", {})
    if limits:
        print(f"    Upstream resources.limits.cpu: {limits.get('cpu', 'N/A')}")
        print(f"    Upstream resources.limits.memory: {limits.get('memory', 'N/A')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <version> (e.g. v2.19.1)")
        sys.exit(1)

    version = sys.argv[1]
    image_tag = version.lstrip("v")
    chart_dir = Path(__file__).resolve().parent.parent

    raw = download_manifest(version)

    print("==> Processing manifest documents...")
    deployment_doc = process_documents(raw, version, chart_dir)

    update_chart_yaml(chart_dir, version)
    update_values_yaml(chart_dir, image_tag)
    print_summary(deployment_doc, chart_dir)

    print()
    print("==> Done! Review changes with:")
    print(f"    git diff {chart_dir.name}/")


if __name__ == "__main__":
    main()
