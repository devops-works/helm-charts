{{/*
Expand the name of the chart.
*/}}
{{- define "thanos.name" -}}
thanos
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "thanos.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "thanos.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "thanos.labels" -}}
helm.sh/chart: {{ include "thanos.chart" . }}
app.kubernetes.io/name: {{ include "thanos.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "thanos.selectorLabels" -}}
app.kubernetes.io/name: {{ include "thanos.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "thanos.image" -}}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag }}
{{- end }}

{{/*
Create objstore config
*/}}
{{- define "thanos.objstoreConfig" -}}
type: {{ .Values.objstoreConfig.type }}
config:
{{ toYaml .Values.objstoreConfig.config | indent 2 }}
{{- end }}

{{/*
Common security context for pods
*/}}
{{- define "thanos.podSecurityContext" -}}
fsGroup: 65534
runAsGroup: 65534
runAsNonRoot: true
runAsUser: 65534
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Common security context for containers
*/}}
{{- define "thanos.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop:
    - ALL
readOnlyRootFilesystem: true
runAsGroup: 65534
runAsNonRoot: true
runAsUser: 65534
seccompProfile:
  type: RuntimeDefault
{{- end }}
