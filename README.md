# AWS Multi-Region EKS + GitOps + DR 프로젝트

<div align="center">

**멀티 리전 EKS 클러스터 구축 및 GitOps 기반 배포 자동화**

[![AWS](https://img.shields.io/badge/AWS-EKS-FF9900?logo=amazon-aws)](https://aws.amazon.com/eks/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.31-326CE5?logo=kubernetes)](https://kubernetes.io/)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?logo=argo)](https://argo-cd.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

</div>

---

## 🎯 프로젝트 개요

AWS 서울, 도쿄, 오사카 3개 리전에 EKS 클러스터를 구축하고, **GitOps 기반의 멀티 리전 운영 환경**과 **DR(Disaster Recovery) 구조**를 구성한 프로젝트입니다.

### 핵심 목표

- ✅ **멀티 리전 EKS 클러스터** 구축 및 운영
- ✅ **GitOps 기반 배포 자동화** (ArgoCD)
- ✅ **Transit Gateway 기반 네트워크 연동**
- ✅ **Staging → Prod → DR** 배포 파이프라인 구축

### 나의 역할

> **오사카 리전 Staging 환경 담당 (First Mover)**

배포를 먼저 검증하고 문제를 사전에 발견하여, 서울 Prod와 도쿄 DR이 참고할 수 있는 **기준 환경을 구축**하는 역할을 수행했습니다.

---

## 🏗️ 아키텍처

### 전체 구조

```
┌────────────────────────────────────────────────────────────────────┐
│              AWS Multi-Region EKS Architecture                     │
└────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
    │  서울 (Prod)     │◄────►│ 오사카 (Staging)   │◄────►│  도쿄 (DR)   │
    │ 192.168.0.0/16  │      │  10.20.0.0/16    │      │10.30.0.0/16 │
    └────────┬────────┘      └────────┬─────────┘      └──────┬──────┘
             │                        │                       │
        ┌────▼────┐              ┌───▼────┐             ┌────▼─────┐
        │ ArgoCD  │              │ board- │             │  Velero  │
        │   Hub   │              │  app   │             │  Backup  │
        │         │              │ Verify │             │  Restore │
        └─────────┘              └────────┘             └──────────┘

    ◄──────────────── Transit Gateway Peering ──────────────────────►
```

### 배포 흐름

```
1. Staging (오사카) → 배포 검증 및 문제 발견
2. Prod (서울) → 실제 서비스 운영
3. DR (도쿄) → 장애 시 복구 대상
```

---

## 💼 나의 역할 및 기여

### 담당 업무

| 구분 | 내용 |
|------|------|
| **리전** | 오사카 (ap-northeast-3) |
| **환경** | Staging |
| **역할** | First Mover - 배포 검증 및 기준 환경 구축 |
| **기간** | 2026.04.28 ~ 2026.04.30 |

### 주요 성과

#### 1. Infrastructure as Code

**오사카 리전 EKS 클러스터 구축**

```yaml
클러스터명: osaka-staging-eks
리전: ap-northeast-3
Kubernetes: 1.31
VPC CIDR: 10.20.0.0/16
노드: t3.medium × 1 (비용 최적화)
```

📁 `infra/eksctl/cluster-c-osaka-staging.yaml`

#### 2. GitOps 매니페스트 작성

**Kustomize 기반 환경별 설정 분리**

```yaml
APP_REGION: osaka
APP_ENV: staging
이미지: 165749212250.dkr.ecr.ap-northeast-3.amazonaws.com/board-app:staging
Replicas: 1
```

📁 `manifests/board-app/overlays/staging/`

#### 3. 컨테이너 이미지 관리

**오사카 리전 ECR 구성 및 이미지 빌드**

- ECR 저장소 생성
- linux/amd64 아키텍처 이미지 빌드
- staging 태그로 버전 관리

#### 4. 배포 검증 자동화

**검증 스크립트 작성**

📁 `scripts/verify-osaka-staging.sh`

- AWS 계정 확인
- Kustomize 렌더링 검증
- 배포 명령어 가이드

#### 5. TGW 네트워크 연동

**오사카 TGW 구성 및 서울 연결**

```
TGW ID: tgw-0e2f5e743241b365b
Route: 192.168.0.0/16 → seoul-osaka-tgw-peering
```

#### 6. 트러블슈팅 및 문서화

| 문제 | 해결 방법 |
|------|----------|
| PVC Pending | EBS CSI Driver 설치 |
| ImagePullBackOff | IAM Role에 ECR 정책 추가 |
| 비용 부담 | 노드 2대 → 1대 축소 |
| DB 연결 실패 | 내부 MySQL Pod 사용 |

📁 `docs/2026.04.29-트러블슈팅-기록.md`

### 측정 가능한 성과

| 지표 | 결과 |
|------|------|
| **클러스터 구축 시간** | 약 20분 (eksctl 자동화) |
| **배포 검증 시간** | 약 5분 (스크립트 자동화) |
| **비용 절감** | 노드 2대 → 1대 (약 50% 절감) |
| **문서화** | 5개 가이드 문서 작성 |
| **트러블슈팅** | 4개 주요 이슈 해결 |

---

## 🛠️ 기술 스택

### Infrastructure

![AWS](https://img.shields.io/badge/AWS-EKS-FF9900?logo=amazon-aws)
![VPC](https://img.shields.io/badge/AWS-VPC-FF9900)
![TGW](https://img.shields.io/badge/AWS-Transit_Gateway-FF9900)
![ECR](https://img.shields.io/badge/AWS-ECR-FF9900)

- Amazon EKS 1.31
- VPC, Transit Gateway, Security Group
- EBS CSI Driver, CloudWatch Logs
- Amazon ECR

### Application

![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)
![Nginx](https://img.shields.io/badge/Nginx-1.27-009639?logo=nginx)

- FastAPI (Python 3.12)
- MySQL 8.0
- Nginx 1.27-alpine
- SQLAlchemy 2.0 (async)

### GitOps & Deployment

![Kubernetes](https://img.shields.io/badge/Kubernetes-1.31-326CE5?logo=kubernetes)
![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?logo=argo)
![Kustomize](https://img.shields.io/badge/Kustomize-Config-326CE5)

- ArgoCD (GitOps)
- Kustomize
- eksctl (IaC)

### Tools

![Docker](https://img.shields.io/badge/Docker-20.10+-2496ED?logo=docker)
![Git](https://img.shields.io/badge/Git-Version_Control-F05032?logo=git)

- Docker
- Git / GitHub
- Bash Script

---

## 📂 프로젝트 구조

```
multi-region-eks-gitops/
├── README.md                          # 프로젝트 개요
│
├── board-app/                         # 샘플 애플리케이션
│   ├── app/                           # FastAPI 애플리케이션
│   ├── Dockerfile                     # 컨테이너 이미지 빌드
│   └── docker-compose.yml             # 로컬 개발 환경
│
├── infra/                             # 인프라 코드
│   ├── eksctl/
│   │   └── cluster-c-osaka-staging.yaml  # 오사카 EKS 설정
│   └── iam_policy.json                # ALB Controller IAM 정책
│
├── manifests/                         # Kubernetes 매니페스트
│   └── board-app/
│       ├── base/                      # 공통 리소스
│       └── overlays/
│           ├── prod/                  # 서울 Prod
│           ├── staging/               # 오사카 Staging
│           └── dr/                    # 도쿄 DR
│
├── argocd-apps/                       # ArgoCD Application 정의
│   ├── app-of-apps.yaml               # App-of-Apps 패턴
│   ├── board-app-prod.yaml            # Prod 앱
│   ├── board-app-staging.yaml         # Staging 앱
│   └── board-app-dr.yaml              # DR 앱
│
├── scripts/                           # 자동화 스크립트
│   └── verify-osaka-staging.sh        # 검증 스크립트
│
└── docs/                              # 프로젝트 문서
    ├── 2026.04.28-EKS-구축-가이드.md
    ├── 2026.04.29-트러블슈팅-기록.md
    ├── 오사카-Staging-클러스터-구축-보고서.md
    ├── ArgoCD-GitOps-가이드.md
    └── AWS-TGW-멀티리전-연결-가이드.md
```

---

## 🚀 빠른 시작

### 1. 클러스터 생성

```bash
# 오사카 Staging 클러스터 생성
eksctl create cluster -f infra/eksctl/cluster-c-osaka-staging.yaml

# kubeconfig 연결
aws eks update-kubeconfig --region ap-northeast-3 --name osaka-staging-eks
```

### 2. 이미지 빌드 및 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-3 | \
  docker login --username AWS --password-stdin \
  165749212250.dkr.ecr.ap-northeast-3.amazonaws.com

# 이미지 빌드 및 푸시
cd board-app
docker build --platform linux/amd64 -t board-app:staging .
docker tag board-app:staging \
  165749212250.dkr.ecr.ap-northeast-3.amazonaws.com/board-app:staging
docker push \
  165749212250.dkr.ecr.ap-northeast-3.amazonaws.com/board-app:staging
```

### 3. 애플리케이션 배포

```bash
# Kustomize로 배포
kubectl apply -k manifests/board-app/overlays/staging

# Pod 상태 확인
kubectl get pods -n board-app-eks -w
```

### 4. 검증

```bash
# 검증 스크립트 실행
./scripts/verify-osaka-staging.sh

# 헬스체크
kubectl exec -it <pod-name> -n board-app-eks -- curl http://localhost:8000/healthz

# 버전 정보 확인
kubectl exec -it <pod-name> -n board-app-eks -- curl http://localhost:8000/version
```

---

## 📚 상세 문서

### 구축 가이드

- 📘 [EKS 구축 가이드](docs/2026.04.28-EKS-구축-가이드.md)
- 📘 [오사카 Staging 클러스터 구축 보고서](docs/오사카-Staging-클러스터-구축-보고서.md)

### 운영 가이드

- 📗 [ArgoCD GitOps 가이드](docs/ArgoCD-GitOps-가이드.md)
- 📗 [AWS TGW 멀티리전 연결 가이드](docs/AWS-TGW-멀티리전-연결-가이드.md)

### 트러블슈팅

- 📕 [트러블슈팅 기록](docs/2026.04.29-트러블슈팅-기록.md)

---

## 💡 학습 및 성장

### 기술 역량 향상

#### Kubernetes & Container Orchestration
- ✅ EKS 클러스터 구축 및 운영
- ✅ Pod, Deployment, Service, Ingress 실무 적용
- ✅ Liveness/Readiness Probe 설계
- ✅ PVC/PV 스토리지 관리

#### GitOps & CI/CD
- ✅ ArgoCD 기반 GitOps 배포
- ✅ Kustomize를 활용한 환경별 설정 분리
- ✅ App-of-Apps 패턴 이해

#### AWS Cloud
- ✅ VPC 네트워크 설계
- ✅ Transit Gateway 멀티 리전 연동
- ✅ ECR 컨테이너 레지스트리 관리
- ✅ IAM Role/Policy 권한 관리

#### Infrastructure as Code
- ✅ eksctl을 활용한 인프라 코드화
- ✅ 재현 가능한 인프라 구축

#### Troubleshooting & Debugging
- ✅ PVC 바인딩 문제 해결
- ✅ 이미지 Pull 권한 문제 해결
- ✅ 네트워크 연결 문제 디버깅

---

**Last Updated**: 2026.04.30
