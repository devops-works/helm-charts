# Update script

Updates the Helm chart to a new upstream version of the RabbitMQ Cluster
Operator by downloading the official manifest from GitHub releases.

## Prerequisites

```
pip install -r requirements.txt
```

## Usage

From the chart root directory:

```
python update-operator.py v2.19.1
```

The script will:

1. Download `cluster-operator.yml` from the GitHub release
2. Extract the CRD into `crds/rabbitmqclusters.yaml`
3. Regenerate one template per kind (namespace and labels templatized for
   Helm, Deployment and ServiceAccount parameterized from `values.yaml`)
4. Update `appVersion` in `Chart.yaml` and `image.tag` in `values.yaml`

Review changes with `git diff` before committing.

Chart-specific templates listed in `PRESERVED_TEMPLATES` are kept as is.
Upstream resources listed in `SKIPPED_RESOURCES` are not rendered.
`image.repository`, the `values.yaml` header and the chart `version` are
not updated: the script prints a warning when the upstream image
repository changes.
