#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELM_ROOT="$ROOT_DIR/helm"
CHART_DIR="$HELM_ROOT/app"
HELM_BIN="${HELM_BIN:-/opt/homebrew/opt/helm@3/bin/helm}"

RELEASE_NAME="${RELEASE_NAME:-foodgram}"
NAMESPACE="${NAMESPACE:-foodgram}"

if [[ -f "$HELM_ROOT/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$HELM_ROOT/.env"
  set +a
elif [[ -f "$ROOT_DIR/deploy/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT_DIR/deploy/.env"
  set +a
fi

export HELM_SECRETS_BACKEND=vals

"$HELM_BIN" dependency build "$CHART_DIR"

"$HELM_BIN" secrets --evaluate-templates -b vals upgrade --install "$RELEASE_NAME" "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --create-namespace \
  -f "$CHART_DIR/values.yaml"
