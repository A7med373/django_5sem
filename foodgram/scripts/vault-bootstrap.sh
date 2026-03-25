#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:-vault}"

echo "Initializing Vault in namespace: $NAMESPACE"
#INIT_JSON="$(kubectl exec -n "$NAMESPACE" vault-0 -- vault operator init -format=json)"
#echo "$INIT_JSON" > vault-init.json

#UNSEAL_KEY="$(python3 -c 'import json;print(json.load(open("vault-init.json"))["unseal_keys_b64"][0])')"
#ROOT_TOKEN="$(python3 -c 'import json;print(json.load(open("vault-init.json"))["root_token"])')"

ROOT_TOKEN="hvs.6Gu0OMLN5S9UDnnBS3Bo6bqs"

#kubectl exec -n "$NAMESPACE" vault-0 -- vault operator unseal "$UNSEAL_KEY"
kubectl exec -n "$NAMESPACE" vault-0 -- vault login "$ROOT_TOKEN"
kubectl exec -n "$NAMESPACE" vault-0 -- vault secrets enable -path=kv kv-v2 || true
kubectl exec -n "$NAMESPACE" vault-0 -- vault kv put kv/foodgram/db postgres-password="postgresmaster"

cat > vault-foodgram-policy.hcl <<'EOF'
path "kv/data/foodgram/*" {
  capabilities = ["read"]
}
EOF

kubectl cp vault-foodgram-policy.hcl "$NAMESPACE"/vault-0:/tmp/vault-foodgram-policy.hcl
kubectl exec -n "$NAMESPACE" vault-0 -- vault policy write foodgram /tmp/vault-foodgram-policy.hcl
kubectl exec -n "$NAMESPACE" vault-0 -- vault auth enable approle || true
kubectl exec -n "$NAMESPACE" vault-0 -- vault write auth/approle/role/foodgram \
  token_policies="foodgram" \
  token_ttl="1h" \
  token_max_ttl="4h"

ROLE_ID="$(kubectl exec -n "$NAMESPACE" vault-0 -- vault read -field=role_id auth/approle/role/foodgram/role-id)"
SECRET_ID="$(kubectl exec -n "$NAMESPACE" vault-0 -- vault write -field=secret_id -f auth/approle/role/foodgram/secret-id)"

echo "Vault bootstrap complete"
echo "ROLE_ID=$ROLE_ID"
echo "SECRET_ID=$SECRET_ID"
echo "Save them into deploy/.env"
