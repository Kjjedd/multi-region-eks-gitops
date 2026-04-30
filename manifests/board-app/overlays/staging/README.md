# Staging Overlay (오사카 리전)

> **담당자**: 김종언 (팀원 B)  
> **리전**: ap-northeast-3 (오사카)  
> **환경**: Staging

---

## 개요

이 overlay는 오사카 리전의 Staging 환경을 위한 Kustomize 설정입니다. base 매니페스트를 기반으로 Staging 환경에 맞게 커스터마이징합니다.

## 주요 변경 사항

### 1. 이미지 설정

```yaml
images:
  - name: 816040392320.dkr.ecr.ap-northeast-2.amazonaws.com/board-app
    newName: 165749212250.dkr.ecr.ap-northeast-3.amazonaws.com/board-app
    newTag: staging
```

- **서울 Prod 이미지** → **오사카 Staging 이미지**로 변경
- 태그: `staging`

### 2. Deployment 패치

```yaml
- op: replace
  path: /spec/replicas
  value: 1
```

- Replicas: `2` → `1` (비용 최적화)

### 3. ConfigMap 패치

```yaml
- op: replace
  path: /data/APP_ENV
  value: staging

- op: replace
  path: /data/APP_REGION
  value: osaka

- op: replace
  path: /data/DB_HOST
  value: mysql
```

- **APP_ENV**: `production` → `staging`
- **APP_REGION**: `ap-northeast-2` → `osaka`
- **DB_HOST**: RDS 엔드포인트 → `mysql` (내부 Pod)

### 4. SecretProviderClass 패치

```yaml
- op: replace
  path: /spec/parameters/objects
  value: |
    - objectName: 'arn:aws:secretsmanager:ap-northeast-3:165749212250:secret:board-app/osaka/staging/db-credentials-kMIxst'
      objectType: secretsmanager
      ...
```

- **Secrets Manager ARN**: 오사카 리전의 시크릿으로 변경

## 배포 방법

### 로컬에서 렌더링 확인

```bash
kubectl kustomize manifests/board-app/overlays/staging
```

### 직접 배포

```bash
kubectl apply -k manifests/board-app/overlays/staging
```

### ArgoCD로 배포

```bash
kubectl apply -f argocd-apps/board-app-staging.yaml
```

## 검증

```bash
# Pod 상태 확인
kubectl get pods -n board-app-eks

# 환경 변수 확인
kubectl exec -it <pod-name> -n board-app-eks -- env | grep APP_

# 버전 정보 확인
kubectl exec -it <pod-name> -n board-app-eks -- curl http://localhost:8000/version
```

예상 응답:
```json
{
  "version": "1",
  "region": "osaka",
  "env": "staging",
  "hostname": "board-app-xxx"
}
```

## 주의사항

1. **DB 연결**: 내부 MySQL Pod 사용 (RDS 아님)
2. **Replicas**: 비용 절감을 위해 1개로 설정
3. **Secrets Manager**: 오사카 리전의 시크릿 사용
4. **ECR**: 오사카 리전의 ECR 레지스트리 사용

## 관련 문서

- [오사카 Staging 클러스터 구축 보고서](../../../docs/오사카-Staging-클러스터-구축-보고서.md)
- [트러블슈팅 기록](../../../docs/2026.04.29-트러블슈팅-기록.md)
