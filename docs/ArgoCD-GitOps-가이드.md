# ArgoCD GitOps 가이드

> Hub-Spoke 패턴으로 멀티 리전 EKS 클러스터를 GitOps 방식으로 관리

## 아키텍처

```
GitHub Repository (manifests)
      ↓ (sync)
ArgoCD Hub (서울 EKS)
      ↓ (deploy)
├── 서울 Prod (로컬)
├── 오사카 Staging (원격)
└── 도쿄 DR (원격)
```

## Git Repository 구조

```
manifests/
└── board-app/
    ├── base/                   # 공통 리소스
    │   ├── Namespace.yaml
    │   ├── Deployment.yaml
    │   ├── Service.yaml
    │   ├── Ingress.yaml
    │   ├── Configmap.yaml
    │   ├── SecretProviderClass.yaml
    │   └── kustomization.yaml
    └── overlays/
        ├── prod/               # 서울 (replicas: 2)
        ├── staging/            # 오사카 (replicas: 1)
        └── dr/                 # 도쿄 (replicas: 1)
```

## ArgoCD 설치 (서울 Hub)

## ArgoCD 설치 (서울 Hub)

```bash
# 설치
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# LoadBalancer로 노출
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# 초기 비밀번호 확인
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d
```

### CLI 설치 및 로그인

```bash
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && mv argocd /usr/local/bin/

argocd login <ARGOCD_SERVER_URL> --username admin --password <패스워드> --insecure
```

### GitHub Repository 연동

```bash
argocd repo add https://github.com/<계정>/<repo>.git \
  --username <username> \
  --password <GitHub Personal Access Token>
```

## Spoke 클러스터 등록

### kubeconfig 가져오기

```bash
aws eks update-kubeconfig --region ap-northeast-1 --name tokyo-dr-eks
aws eks update-kubeconfig --region ap-northeast-3 --name osaka-staging-eks
```

### ArgoCD에 등록

```bash
argocd cluster add <도쿄-context-name> --name tokyo-dr-eks
argocd cluster add <오사카-context-name> --name osaka-staging-eks
```

## Application 생성 (App of Apps 패턴)

## Application 생성 (App of Apps 패턴)

여러 환경을 한 번에 관리하는 상위 Application:

```yaml
# app-of-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-of-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<계정>/<repo>.git
    targetRevision: main
    path: argocd-apps/
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**배포**:
```bash
kubectl apply -f argocd-apps/app-of-apps.yaml
```

이 명령 하나로 모든 환경(Prod, Staging, DR)이 자동 배포됩니다.

## 배포 확인

```bash
# Application 목록
argocd app list

# 상세 상태
argocd app get board-app-staging

# 수동 sync
argocd app sync board-app-staging
```

## GitOps 배포 흐름

```
1. 코드/YAML 수정
    ↓
2. git push → GitHub
    ↓
3. ArgoCD 변경 감지 (3분 폴링)
    ↓
4. 자동 sync → EKS 반영
```

### Webhook 설정 (즉시 반영)

GitHub Repo → Settings → Webhooks:
- **Payload URL**: `https://<ARGOCD_SERVER_URL>/api/webhook`
- **Content type**: `application/json`
- **Events**: Just the push event

## 주요 설정

### Sync Policy

```yaml
syncPolicy:
  automated:
    prune: true      # 삭제된 리소스 자동 제거
    selfHeal: true   # 수동 변경 시 자동 복구
  syncOptions:
    - CreateNamespace=true
    - PruneLast=true  # 삭제는 마지막에 수행
```

### Secret 관리

❌ **하지 말 것**: Secret.yaml을 Git에 올리기

✅ **권장 방법**:
- Secrets Manager + SecretProviderClass
- Sealed Secrets
- External Secrets Operator

---

## 참고 자료

- [ArgoCD 공식 문서](https://argo-cd.readthedocs.io/)
- [Kustomize 공식 문서](https://kustomize.io/)
- [App of Apps Pattern](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/)
