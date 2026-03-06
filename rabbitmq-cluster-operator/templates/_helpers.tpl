{{/*
Common labels
*/}}
{{- define "rabbitmq-cluster-operator.labels" -}}
app.kubernetes.io/component: rabbitmq-operator
app.kubernetes.io/name: rabbitmq-cluster-operator
app.kubernetes.io/part-of: rabbitmq
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

{{/*
Selector labels (used by Deployment matchLabels)
*/}}
{{- define "rabbitmq-cluster-operator.selectorLabels" -}}
app.kubernetes.io/name: rabbitmq-cluster-operator
{{- end }}
