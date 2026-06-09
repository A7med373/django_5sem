# HW 8. CI/CD

## Что реализовано

- Semantic-release настраивает версионирование по conventional commits и создает Git tag формата `vX.Y.Z`.
- GitHub Actions workflow `.github/workflows/ci-cd.yml`:
  - запускает semantic-release;
  - собирает backend и frontend Docker-образы из release tag;
  - публикует образы в GitHub Container Registry;
  - деплоит Helm chart в Kubernetes на self-hosted runner.
- Workflow `.github/workflows/self-hosted-runner-check.yml` проверяет, что runner подключен к проекту.
- Helm values для runner scale set лежит в `helm/runner/values.yaml`.

## Требования к commit messages

Semantic-release создает новый релиз только при conventional commits:

```text
feat: add favorites API
fix: repair recipe serializer
perf: optimize query count
```

Для major release:

```text
feat!: change public API
```

## Secrets GitHub Actions

Для пайплайна нужны secrets:

| Secret | Назначение |
| --- | --- |
| `GITHUB_TOKEN` | Встроенный токен GitHub Actions, используется для release и GHCR |
| `KUBECONFIG_B64` | Base64 kubeconfig для доступа к кластеру, если runner не имеет локального kubeconfig |
| `VAULT_ADDR` | Адрес Vault для `helm-secrets`/`vals` |
| `VAULT_TOKEN` | Token Vault для чтения `ref+vault://...` из Helm values |

`KUBECONFIG_B64` можно получить так:

```bash
base64 -i ~/.kube/config | tr -d '\n'
```

## Установка self-hosted runner через Helm

GitHub рекомендует Actions Runner Controller и chart `gha-runner-scale-set`.

1. Создать namespace:

```bash
kubectl create namespace arc-system
kubectl create namespace arc-runners
```

2. Установить controller:

```bash
helm upgrade --install arc \
  --namespace arc-system \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
```

3. Подготовить token для регистрации runner. Для учебного проекта проще использовать fine-grained PAT с доступом к репозиторию и управлением Actions runners.

4. Создать Kubernetes secret с token:

```bash
kubectl create secret generic foodgram-runner-github-token \
  --namespace arc-runners \
  --from-literal=github_token='<PAT>'
```

5. Скопировать values и заменить:

- `githubConfigUrl` на URL репозитория;
- `githubConfigSecret`, если secret называется иначе.

6. Установить runner scale set:

```bash
helm upgrade --install foodgram \
  --namespace arc-runners \
  --create-namespace \
  -f helm/runner/values.yaml \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

7. Проверить runner:

```bash
kubectl -n arc-runners get pods
```

В GitHub UI runner должен появиться в `Settings -> Actions -> Runners`.

## Запуск пайплайна на runner

1. Открыть GitHub Actions.
2. Запустить workflow `Self-hosted runner check` вручную.
3. Убедиться, что job выполнился на runner scale set `foodgram`.
4. После merge/push в `main` или `master` workflow `Foodgram CI/CD` создаст release tag, соберет образы и выполнит деплой.

## Образы

Release `vX.Y.Z` публикует:

```text
ghcr.io/<owner>/<repo>/backend:vX.Y.Z
ghcr.io/<owner>/<repo>/frontend:vX.Y.Z
ghcr.io/<owner>/<repo>/backend:latest
ghcr.io/<owner>/<repo>/frontend:latest
```

При деплое эти значения передаются в Helm через `--set`, поэтому локальный `helm/app/values.yaml` остается пригодным для ручного запуска.
