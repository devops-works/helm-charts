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
3. Regenerate RBAC templates with upstream rules (namespace and labels
   templatized for Helm)
4. Update `appVersion` in `Chart.yaml` and `image.tag` in `values.yaml`

Review changes with `git diff` before committing.

`templates/deployment.yaml` and `templates/serviceaccount.yaml` are not
auto-updated since they contain Helm-specific parameterization. Review
the script output for upstream changes to these resources.
