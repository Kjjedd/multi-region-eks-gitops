# 오사카 Staging 클러스터 구축 보고서

> **담당 리전**: 오사카 (ap-northeast-3)  
> **역할**: Staging 환경 구축 및 검증  
> **기간**: 2026.04.28 ~ 2026.04.30

---

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [인프라 구성](#인프라-구성)
- [GitOps 매니페스트](#gitops-매니페스트)
- [배포 검증](#배포-검증)
- [트러블슈팅](#트러블슈팅)
- [성과 및 기여](#성과-및-기여)

---

## 프로젝트 개요

### 전체 아키텍처

```
서울 (Prod + Hub)  ←→  오사카 (Staging)  ←→  도쿄 (DR)
192.168.0.0/16         10.20.0.0/16          10.30.0.0/16

- ArgoCD Hub           - 배포 검증           - 백업/복원
- 실제 서비스          - 문제 사전 발견      - Standby
```

### 핵심 미션

> **배포를 먼저 검증하고 문제를 미리 잡아내는 테스트 클러스터를 구축하여, 서울 Prod와 도쿄 DR이 참고할 기준 환경을 만드는 역할**

---

## 인프라 구성

### EKS 클러스터 설정

```yaml
클러스터명: osaka-staging-eks
리전: ap-northeast-3
Kubernetes 버전: 1.31
VPC CIDR: 10.20.0.0/16
노드: t3.medium × 1 (비용 최적화)
관리 방식: eksctl (IaC)
```

### 네트워크 구성

```yaml
Public Subnets:
  - 10.20.0.0/20 (ap-northeast-3a)
  - 10.20.16.0/20 (ap-northeast-3c)

Private Subnets:
  - 10.20.32.0/20 (ap-northeast-3a)
  - 10.20.48.0/20 (ap-northeast-3c)

NAT Gateway: Single (비용 최적화)
```

### 주요 설정

- ✅ OIDC Provider 활성화 (IRSA 지원)
- ✅ CloudWatch Logging 전체 활성화
- ✅ EBS CSI Driver 설치
- ✅ Private Networking (보안)

📁 `infra/eksctl/cluster-c-osaka-staging.yaml`

---

## GitOps 매니페스트

### Kustomize Overlay 구조

📁 `manifests/board-app/overlays/staging/`

```yaml
# 환경 변수
APP_REGION: osaka
APP_ENV: staging

# 이미지
newName: 165749212250.dkr.ecr.ap-northeast-3.amazonaws.com/board-app
newTag: staging

# 리소스
replicas: 1
```

### 주요 패치

1. **Deployment**: Replicas 2 → 1 (비용 최적화)
2. **ConfigMap**: APP_REGION=osaka, APP_ENV=staging
3. **SecretProviderClass**: 오사카 리전 Secrets Manager ARN

---

## 배포 검증

### 검증 스크립트

📁 `scripts/verify-osaka-staging.sh`

```bash
1. AWS 계정 확인
2. 도구 버전 확인
3. Kustomize 렌더링 검증
4. eksctl 설정 파일 검증
5. kubectl context 확인
6. 배포 명령어 가이드
```

### 검증 항목

- ✅ 클러스터 생성 및 노드 Ready
- ✅ 시스템 파드 정상 동작
- ✅ 애플리케이션 배포 성공
- ✅ Liveness/Readiness 헬스체크
- ✅ 응답 헤더 확인 (region=osaka, env=staging)
- ✅ PVC 바인딩 확인

---

## 트러블슈팅

### 주요 이슈 및 해결

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| **PVC Pending** | EBS CSI Driver 미설치 | eksctl addon 설치 |
| **ImagePullBackOff** | ECR 권한 없음 | IAM Role에 ECR 정책 추가 |
| **비용 부담** | 노드 2대 운영 | desired capacity 1로 축소 |
| **DB 연결 실패** | RDS Private 접근 불가 | 내부 MySQL Pod 사용 |

📁 `docs/2026.04.29-트러블슈팅-기록.md`

---

## 성과 및 기여

### 기술적 성과

1. ✅ **Infrastructure as Code**: eksctl YAML로 재현 가능한 인프라 구축
2. ✅ **GitOps 패턴**: Kustomize 기반 환경별 설정 분리
3. ✅ **컨테이너 이미지 관리**: 리전별 ECR 구성 및 이미지 빌드
4. ✅ **자동화**: 검증 스크립트로 배포 프로세스 표준화
5. ✅ **비용 최적화**: 리소스 최소화 및 클러스터 라이프사이클 관리
6. ✅ **네트워크 설계**: 멀티 리전 TGW 연동 준비
7. ✅ **문제 해결**: 실제 배포 중 발생한 이슈 해결 경험

### 팀에 제공한 가치

1. **First Mover Advantage**: 가장 먼저 배포를 완료하여 다른 팀원들이 참고할 수 있는 기준 제공
2. **트러블슈팅 가이드**: 실제 발생한 문제와 해결 방법 문서화
3. **Best Practice**: Kustomize 패턴, 비용 최적화, 검증 자동화 등 모범 사례 제시
4. **네트워크 설계**: CIDR 충돌 없는 VPC 설계로 TGW 연동 기반 마련

### 측정 가능한 성과

| 지표 | 결과 |
|------|------|
| **클러스터 구축 시간** | 약 20분 (eksctl 자동화) |
| **배포 검증 시간** | 약 5분 (스크립트 자동화) |
| **비용 절감** | 노드 2대 → 1대 (약 50% 절감) |
| **문서화** | 5개 가이드 문서 작성 |
| **트러블슈팅** | 4개 주요 이슈 해결 |

---

## 결론

오사카 Staging 클러스터 구축 프로젝트를 통해 **실제 프로덕션 환경에 가까운 멀티 리전 EKS 운영 경험**을 쌓을 수 있었습니다.

특히 **First Mover로서 다른 팀원들이 참고할 수 있는 기준 환경을 제공**하고, **실제 발생한 문제들을 해결하며 트러블슈팅 가이드를 작성**한 것이 큰 성과였습니다.

---

**Last Updated**: 2026.04.30
