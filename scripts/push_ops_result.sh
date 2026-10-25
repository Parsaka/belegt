#!/usr/bin/env bash
# Publish a run's summary files to the ops-results branch:
#
#   bash scripts/push_ops_result.sh <kind> <file-or-dir>...
#
# The development sandbox cannot read Actions logs, so workflows push what matters (Terraform
# results, row counts, dbt test results, bytes processed) here. Only summaries, never data
# files. Each run gets runs/<kind>/<UTC time>-<run id>/.
set -euo pipefail

kind="$1"
shift
stage="$(mktemp -d)"
for f in "$@"; do
  [ -e "$f" ] && cp -r "$f" "$stage"/
done

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
work="$(mktemp -d)"
if git fetch -q --depth=1 origin ops-results; then
  git worktree add -q "$work" FETCH_HEAD
  git -C "$work" checkout -q -B ops-results
else
  git worktree add -q --detach "$work"
  git -C "$work" checkout -q --orphan ops-results
  git -C "$work" rm -rq --cached --ignore-unmatch . >/dev/null
  find "$work" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
fi

dest="runs/${kind}/$(date -u +%Y-%m-%dT%H%M)-${GITHUB_RUN_ID:-local}"
mkdir -p "$work/$dest"
cp -r "$stage"/. "$work/$dest"/
printf 'run %s (%s) on %s @ %s\n' "${GITHUB_RUN_ID:-local}" "${GITHUB_WORKFLOW:-}" \
  "${GITHUB_REF_NAME:-}" "${GITHUB_SHA:-}" > "$work/$dest/RUN.txt"

git -C "$work" add runs
git -C "$work" commit -qm "${kind}: run ${GITHUB_RUN_ID:-local}"
for attempt in 1 2 3; do  # two workflows may push at the same time
  git -C "$work" push -q origin ops-results && exit 0
  git -C "$work" fetch -q --depth=1 origin ops-results
  git -C "$work" rebase -q FETCH_HEAD
  sleep $((attempt * 3))
done
exit 1
