{{- define "belegt-reports.labels" -}}
app.kubernetes.io/name: belegt-reports
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
{{- define "belegt-reports.rows" -}}
{{- if not (trim .Values.seed) -}}
{{- fail "set the report list with --set-file seed=dbt/seeds/reports.csv" -}}
{{- end -}}
{{- sub (len (splitList "\n" (trim .Values.seed))) 1 -}}
{{- end -}}
