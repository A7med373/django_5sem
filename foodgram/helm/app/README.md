# Umbrella chart `app`

Matches the course layout: **`charts/back`**, **`charts/front`**, **`charts/postgres`**, parent **`templates/ingress.yaml`**, secrets/refs in **`values.yaml`**.

- Docker images default to **`a7med373/foodgram-st`** and **`a7med373/foodgram-frontend-st`**.
- **Frontend** nginx proxies to **`back-service:8000`** (Service from subchart `back`).
- **Ingress** targets **`global.serviceName.front`** (default `foodgram-frontend-service`).
- **DB**: ConfigMap name **`global.config.name`** (`db-config`), Secret **`global.secret.name`** (`db-secret`), keys `postgres-name` / `postgres-user` / `postgres-password` (see `postgres` subchart).
- **`helm test`** includes `charts/postgres/templates/tests/test-connection.yaml` (TCP check with `nc`).

```bash
HELM=/opt/homebrew/opt/helm@3/bin/helm
cd "$(dirname "$0")"
$HELM dependency build .
$HELM lint .
```
