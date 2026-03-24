#!/usr/bin/env bash
set -euo pipefail

# Run from repo: foodgram/helm/
cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ -f .env ]]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

HELM_BIN="${HELM_BIN:-/opt/homebrew/opt/helm@3/bin/helm}"
RELEASE_NAME="${RELEASE_NAME:-foodgram}"
NAMESPACE="${NAMESPACE:-foodgram}"

export HELM_SECRETS_BACKEND=vals

"$HELM_BIN" dependency build app

# Same flags as reference: evaluate-templates + vals backend
"$HELM_BIN" secrets --evaluate-templates -b vals upgrade --install "$RELEASE_NAME" app \
  --namespace "$NAMESPACE" \
  --create-namespace \
  -f app/values.yaml
