#!/usr/bin/env bash
# Runs the report Indexed Job on kind against made-up statements served inside the cluster:
# two good reports and one host that answers with HTML. Expects the two good tasks to finish
# with their figures and only the broken task to fail, after its own retries.
set -euo pipefail
IMAGE_TAG=${IMAGE_TAG:-ci}
work=$(mktemp -d)

python - "$work" <<'PY'
import sys
from pathlib import Path
from belegt.documents.synthetic import statement

out = Path(sys.argv[1]) / "pdfs"
out.mkdir()
(out / "alpha.pdf").write_bytes(statement("Alpha AG", "12,5", "1,0", "40,0"))
(out / "beta.pdf").write_bytes(statement("Beta AG", "0,8", "0,2", "3,1"))
(out / "broken.pdf").write_text("<!DOCTYPE html><p>Please accept cookies</p>")
PY

kubectl create configmap pdfs --from-file="$work/pdfs"
kubectl apply -f - <<YAML
apiVersion: v1
kind: Pod
metadata: {name: pdf-server, labels: {app: pdf-server}}
spec:
  containers:
    - name: http
      image: belegt-reports:${IMAGE_TAG}
      command: [python, -m, http.server, "8000", --directory, /srv]
      ports: [{containerPort: 8000}]
      volumeMounts: [{name: pdfs, mountPath: /srv}]
  volumes: [{name: pdfs, configMap: {name: pdfs}}]
---
apiVersion: v1
kind: Service
metadata: {name: pdf-server}
spec:
  selector: {app: pdf-server}
  ports: [{port: 8000}]
YAML
kubectl wait --for=condition=Ready pod/pdf-server --timeout=2m

cat > "$work/seed.csv" <<CSV
doc_id,company,lei,report_year,fiscal_year_end,language,url,host_note
alpha-2024,Alpha AG,5299000000000000ALPH,2024,12-31,de,http://pdf-server:8000/alpha.pdf,kind
beta-2024,Beta AG,5299000000000000BETA,2024,12-31,de,http://pdf-server:8000/beta.pdf,kind
broken-2024,Broken AG,5299000000000000BROK,2024,12-31,de,http://pdf-server:8000/broken.pdf,kind
CSV

helm install smoke deploy/helm/belegt-reports \
  --set image.tag="$IMAGE_TAG" --set runId=kind --set backoffLimitPerIndex=1 \
  --set 'networkPolicy.extraEgressPorts={8000}' \
  --set-file seed="$work/seed.csv"

job=job/smoke-reports-kind
kubectl wait "$job" --for=condition=Failed --timeout=5m
completed=$(kubectl get "$job" -o jsonpath='{.status.completedIndexes}')
failed=$(kubectl get "$job" -o jsonpath='{.status.failedIndexes}')
echo "completed indexes: $completed, failed indexes: $failed"
test "$completed" = "0,1"
test "$failed" = "2"

logs() {
  kubectl logs -l "batch.kubernetes.io/job-completion-index=$1,app.kubernetes.io/instance=smoke" \
    --tail=1 | tail -1
}
logs 0 | jq -e '.doc_id == "alpha-2024" and .selected.scope1 == 12500000 and .pages == 3'
logs 1 | jq -e '.doc_id == "beta-2024" and .selected.scope1 == 800000'
logs 2 | jq -e '.doc_id == "broken-2024" and (.error | contains("did not return a PDF"))'
echo "kind: report Indexed Job OK"
