# ArgoCD Applications

> App-of-Apps 패턴으로 멀티 리전 배포 관리

## 구조

```
app-of-apps.yaml (서울 ArgoCD Hub)
    ├── board-app-prod.yaml (서울 Prod)
    ├── board-app-staging.yaml (오사카 Staging) ← 본인 담당
    └── board-app-dr.yaml (도쿄 DR)
```

## 파일 설명

### app-of-apps.yaml
모든 환경을 한 번에 관리하는 루트 Application

### board-app-prod.yaml
서울 Prod 환경 (로컬 클러스터)

### board-app-staging.yaml
**담당자**: 김종언 (팀원 B)

오사카 Staging 환경 (원격 클러스터)
- 서울 ArgoCD Hub에서 원격 관리
- Kustomize overlay로 리전별 설정 적용

### board-app-dr.yaml
도쿄 DR 환경 (원격 클러스터)

## 배포 방법

```bash
# 1. ArgoCD 설치 (서울 Hub)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. 원격 클러스터 등록
argocd cluster add osaka-staging-eks --name osaka-staging
argocd cluster add tokyo-dr-eks --name tokyo-dr

# 3. App-of-Apps 배포 (모든 환경 자동 배포)
kubectl apply -f argocd-apps/app-of-apps.yaml
```

## Sync Policy

```yaml
syncPolicy:
  automated:
    prune: true      # 삭제된 리소스 자동 제거
    selfHeal: true   # 수동 변경 시 자동 복구
  syncOptions:
    - CreateNamespace=true
```

## 확인 방법

```bash
# Application 목록
argocd app list

# Staging 앱 상태
argocd app get board-app-staging

# 동기화
argocd app sync board-app-staging
```

---

**관련 문서**: [ArgoCD GitOps 가이드](../docs/ArgoCD-GitOps-가이드.md)
