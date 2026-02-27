{{/*
Keycloak Helm Chart Helpers
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "keycloak.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "keycloak.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Return the namespace
*/}}
{{- define "keycloak.namespace" -}}
{{- default .Release.Namespace .Values.namespaceOverride }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "keycloak.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Standard labels
*/}}
{{- define "keycloak.labels" -}}
helm.sh/chart: {{ include "keycloak.chart" . }}
{{ include "keycloak.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "keycloak.selectorLabels" -}}
app.kubernetes.io/name: {{ include "keycloak.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "keycloak.image" -}}
{{- $registry := .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if .Values.image.digest }}
{{- printf "%s/%s@%s" $registry $repository .Values.image.digest }}
{{- else }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image pull secrets
*/}}
{{- define "keycloak.imagePullSecrets" -}}
{{- if .Values.image.pullSecrets }}
imagePullSecrets:
{{- range .Values.image.pullSecrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "keycloak.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "keycloak.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the path Keycloak is hosted on with trailing slash
*/}}
{{- define "keycloak.httpPath" -}}
{{- if hasSuffix "/" .Values.httpRelativePath }}
{{- .Values.httpRelativePath }}
{{- else }}
{{- printf "%s/" .Values.httpRelativePath }}
{{- end }}
{{- end }}

{{/*
Return the secret containing the Keycloak admin password
*/}}
{{- define "keycloak.secretName" -}}
{{- if .Values.auth.existingSecret }}
{{- tpl .Values.auth.existingSecret $ }}
{{- else }}
{{- include "keycloak.fullname" . }}
{{- end }}
{{- end }}

{{/*
Return the secret key that contains the Keycloak admin password
*/}}
{{- define "keycloak.secretKey" -}}
{{- if and .Values.auth.existingSecret .Values.auth.passwordSecretKey }}
{{- .Values.auth.passwordSecretKey }}
{{- else }}
{{- print "admin-password" }}
{{- end }}
{{- end }}

{{/*
Return the Database hostname
*/}}
{{- define "keycloak.databaseHost" -}}
{{- tpl .Values.externalDatabase.host $ }}
{{- end }}

{{/*
Return the Database port
*/}}
{{- define "keycloak.databasePort" -}}
{{- .Values.externalDatabase.port | quote }}
{{- end }}

{{/*
Return the Database name
*/}}
{{- define "keycloak.databaseName" -}}
{{- .Values.externalDatabase.database }}
{{- end }}

{{/*
Return the Database user
*/}}
{{- define "keycloak.databaseUser" -}}
{{- .Values.externalDatabase.user }}
{{- end }}

{{/*
Return the Database secret name
*/}}
{{- define "keycloak.databaseSecretName" -}}
{{- if .Values.externalDatabase.existingSecret }}
{{- tpl .Values.externalDatabase.existingSecret $ }}
{{- else }}
{{- printf "%s-externaldb" .Release.Name }}
{{- end }}
{{- end }}

{{/*
Return the Database password key
*/}}
{{- define "keycloak.databaseSecretPasswordKey" -}}
{{- if and .Values.externalDatabase.existingSecret .Values.externalDatabase.existingSecretPasswordKey }}
{{- .Values.externalDatabase.existingSecretPasswordKey }}
{{- else }}
{{- print "db-password" }}
{{- end }}
{{- end }}

{{/*
Render a value that may contain templates
*/}}
{{- define "keycloak.render" -}}
{{- if typeIs "string" .value }}
{{- tpl .value .context }}
{{- else }}
{{- tpl (.value | toYaml) .context }}
{{- end }}
{{- end }}

{{/*
Generate a random password if not provided
*/}}
{{- define "keycloak.randomPassword" -}}
{{- $secret := lookup "v1" "Secret" .namespace .secretName -}}
{{- if $secret }}
{{- index $secret.data .key | b64dec }}
{{- else if .providedValue }}
{{- .providedValue }}
{{- else }}
{{- randAlphaNum .length }}
{{- end }}
{{- end }}

{{/*
Validate values
*/}}
{{- define "keycloak.validateValues" -}}
{{- $messages := list -}}
{{- if and (not .Values.externalDatabase.host) (not .Values.externalDatabase.existingSecret) }}
{{- $messages = append $messages "externalDatabase.host is required when not using existingSecret" }}
{{- end }}
{{- if empty .Values.proxyHeaders }}
{{- $messages = append $messages "proxyHeaders is required (e.g. 'xforwarded')" }}
{{- end }}
{{- if $messages }}
{{- fail (printf "\nVALIDATION ERRORS:\n%s" (join "\n" $messages)) }}
{{- end }}
{{- end }}

{{/*
Security context - removes fields not allowed in certain environments
*/}}
{{- define "keycloak.securityContext" -}}
{{- $sc := .secContext -}}
{{- if $sc.enabled }}
{{- omit $sc "enabled" | toYaml }}
{{- end }}
{{- end }}
