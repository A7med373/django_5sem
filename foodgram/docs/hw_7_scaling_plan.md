# Homework 7: Scaling Report

## Goal

Configure metrics, resource limits, load testing, HPA, VPA, and Locust deployment for the Foodgram API.

## Implemented files

- Backend resources: `foodgram/helm/app/charts/back/templates/deployment.yaml`
- Backend HPA: `foodgram/helm/app/charts/back/templates/hpa.yaml`
- Backend VPA: `foodgram/helm/app/charts/back/templates/vpa.yaml`
- Backend values: `foodgram/helm/app/charts/back/values.yaml`
- Umbrella chart values: `foodgram/helm/app/values.yaml`
- Locust chart: `foodgram/helm/locust`
- PostgreSQL secret template fix: `foodgram/helm/app/charts/postgres/templates/secret-template.yaml`

## Part 1. Metrics and initial resources

`metrics-server` was enabled in minikube and verified with:

```bash
kubectl top nodes
kubectl top pods -n foodgram
```

Initial backend resources:

```yaml
requests:
  cpu: 200m
  memory: 256Mi
limits:
  cpu: 500m
  memory: 512Mi
```

Observed idle backend usage was low, about `1m CPU` and `59-73Mi memory` per pod. Under load, backend memory stayed below the configured request.

## Part 2. Locust stress test

Locust tests cover public API endpoints:

- `GET /api/recipes/`
- `GET /api/ingredients/?name=[query]`
- `GET /api/recipes/1/`

The invalid `/api/tags/` endpoint was removed from the test because it does not exist in this project.

Current Locust defaults:

```yaml
users: 300
spawnRate: 50
runTime: 5m
workers: 2
host: http://back-service:8000
```

A corrected test run produced `0.00%` failures. During the first `100` user test, the average response time was far below the required `5-7s` threshold.

## Part 3. HPA and VPA

HPA is configured for the backend Deployment:

```yaml
minReplicas: 3
maxReplicas: 8
targetCPUUtilizationPercentage: 50
```

Scale behavior:

```yaml
scaleUp:
  stabilizationWindowSeconds: 0
scaleDown:
  stabilizationWindowSeconds: 300
```

The target was tuned from `70%` to `50%` so the local minikube environment could demonstrate scale-up with the available load generator capacity.

HPA was verified:

```bash
kubectl get hpa back-hpa -n foodgram
kubectl describe hpa back-hpa -n foodgram
```

Observed HPA behavior:

- `back-deployment` scaled from `3` to `5` pods under load.
- After the `300s` stabilization window, it scaled back from `5` to `3` pods.

Observed HPA events:

```text
New size: 5; reason: cpu resource utilization (percentage of request) above target
New size: 3; reason: All metrics below target
```

VPA is configured in recommendation-only mode:

```yaml
updateMode: "Off"
controlledResources:
  - cpu
  - memory
```

VPA was verified:

```bash
kubectl describe vpa back-vpa -n foodgram
```

Observed recommendation:

```text
CPU: 163m
Memory: 250Mi
RecommendationProvided: True
```

The current backend memory request `256Mi` matches the observed VPA memory recommendation closely.

## Part 4. Locust deployment

`locust-operator` is installed in the cluster. The local operator uses:

```yaml
apiVersion: locust.cloud/v1
kind: LocustTest
```

The Helm chart `foodgram/helm/locust` deploys:

- `ConfigMap` with `locustfile.py`
- `LocustTest` named `load-test-v2`
- `Ingress` named `load-test-v2-webui`

The Ingress points to the operator-created service:

```yaml
service:
  name: load-test-v2-webui
  port: 8089
```

Deploy command:

```bash
helm upgrade --install load-test ./foodgram/helm/locust -n foodgram
```

Verification:

```bash
kubectl get locusttests -n foodgram
kubectl get svc load-test-v2-webui -n foodgram
kubectl get pods -n foodgram
```

## Vault note

Vault was sealed after minikube restart. The previous local `vault-init.json` did not match the active Vault storage, so the local Vault instance was recreated.

Current state:

- Vault is initialized.
- Vault is unsealed.
- New init data is stored locally in `foodgram/vault-init.json`.
- AppRole env files are stored locally in `foodgram/helm/.env` and `foodgram/deploy/.env`.
- These files are ignored by git and must not be committed.

For local Helm deploy with Vault refs:

```bash
kubectl port-forward -n vault svc/vault 8200:8200
```

In another terminal:

```bash
cd foodgram/helm
./deploy.sh
```

The deployment was verified successfully:

```text
Release "foodgram" has been upgraded.
Revision: 11
```

## Final status

Checked on 2026-06-08:

- `foodgram` Helm release is deployed.
- Backend rollout is successful.
- HPA is active and currently at `3` replicas.
- VPA provides recommendations.
- Locust operator is installed.
- Locust test chart is installed.
- Vault is unsealed and usable by `helm-secrets`/`vals`.
