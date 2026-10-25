{{- define "belegt-api.name" -}}{{ .Release.Name }}-api{{- end -}}
{{- define "belegt-api.labels" -}}
app.kubernetes.io/name: belegt-api
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "belegt-api.secretName" -}}
{{- .Values.auth.existingSecret | default (printf "%s-tokens" (include "belegt-api.name" .)) -}}
{{- end -}}
