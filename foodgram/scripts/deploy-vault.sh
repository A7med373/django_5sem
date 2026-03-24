#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_VALUES="$ROOT_DIR/deploy/vault-values.yaml"
HELM_BIN="${HELM_BIN:-/opt/homebrew/opt/helm@3/bin/helm}"

"$HELM_BIN" repo add hashicorp https://helm.releases.hashicorp.com
"$HELM_BIN" repo update

"$HELM_BIN" upgrade --install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  -f "$VAULT_VALUES"
