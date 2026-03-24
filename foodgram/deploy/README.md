# Secrets and Vault workflow

## 1) Install required tools

```bash
brew install helm
brew install vals
helm plugin install https://github.com/jkroepke/helm-secrets
```

## 2) Deploy Vault chart

```bash
./scripts/deploy-vault.sh
```

If pulling from the official repo fails with 403, use a mirror:

```bash
helm repo add hashicorp-mirror https://helm-mirror.yandexcloud.net/hashicorp
helm upgrade --install vault hashicorp-mirror/vault \
  --namespace vault --create-namespace \
  -f deploy/vault-values.yaml
```

## 3) Init and unseal Vault, configure KV/AppRole

```bash
./scripts/vault-bootstrap.sh vault
```

Copy printed `ROLE_ID` and `SECRET_ID` into `deploy/.env`.

## 4) Deploy Foodgram with Vault refs

Vault paths live in **`helm/app/values.yaml`** under `postgres.secrets` (`ref+vault://...`). Adjust to your KV mount and keys.

```bash
cp deploy/.env.example deploy/.env
# optional: same variables in helm/.env for helm/deploy.sh
cp helm/.env.example helm/.env
```

```bash
./helm/deploy.sh
# or
./scripts/deploy-foodgram.sh
```

For **helm-secrets** decrypted values, you can add **`helm/app/values.yaml.dec`** (from `helm secrets decrypt`) and pass `-f app/values.yaml.dec` next to `values.yaml`.

## 5) Dry run validation

```bash
/opt/homebrew/opt/helm@3/bin/helm dependency build ./helm/app
/opt/homebrew/opt/helm@3/bin/helm lint ./helm/app

# Plain template (without resolving Vault refs — ok for YAML shape check):
/opt/homebrew/opt/helm@3/bin/helm template foodgram ./helm/app --debug

# Use client-side dry-run to avoid ownership collisions with existing objects
/opt/homebrew/opt/helm@3/bin/helm install foodgram ./helm/app \
  --namespace foodgram-test --create-namespace \
  --dry-run=client --debug
```
