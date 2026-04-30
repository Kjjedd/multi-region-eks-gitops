# Infrastructure

> EKS 클러스터 및 인프라 구성 코드

## 구조

```
infra/
├── eksctl/
│   └── cluster-c-osaka-staging.yaml  # 오사카 Staging EKS 설정 (본인 작성)
└── iam_policy.json                   # AWS Load Balancer Controller IAM 정책
```

## cluster-c-osaka-staging.yaml

**담당자**: 김종언 (팀원 B)

오사카 리전 Staging EKS 클러스터 IaC 정의

**주요 설정**:
- 클러스터명: osaka-staging-eks
- 리전: ap-northeast-3
- Kubernetes: 1.31
- VPC CIDR: 10.20.0.0/16
- 노드: t3.medium × 1 (비용 최적화)
- OIDC Provider 활성화 (IRSA 지원)
- Private Networking (보안)
- NAT Gateway Single (비용 절감)

**생성**:
```bash
eksctl create cluster -f infra/eksctl/cluster-c-osaka-staging.yaml
```

**삭제**:
```bash
eksctl delete cluster --name osaka-staging-eks --region ap-northeast-3
```

## iam_policy.json

AWS Load Balancer Controller IAM 정책

**사용 방법**:

```bash
# 1. IAM 정책 생성
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://infra/iam_policy.json

# 2. IRSA 생성
eksctl create iamserviceaccount \
  --cluster=osaka-staging-eks \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::<ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=ap-northeast-3

# 3. Helm 설치
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=osaka-staging-eks \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=ap-northeast-3 \
  --set vpcId=<VPC_ID>
```

## 네트워크 설계

| 리전 | VPC CIDR | 역할 | 담당자 |
|------|----------|------|--------|
| 서울 | 192.168.0.0/16 | Prod + Hub | 김재현 |
| 오사카 | 10.20.0.0/16 | Staging | 김종언 (본인) |
| 도쿄 | 10.30.0.0/16 | DR | 백시관 |

**오사카 서브넷 구성**:
```
VPC: 10.20.0.0/16
Public:  10.20.0.0/20, 10.20.16.0/20
Private: 10.20.32.0/20, 10.20.48.0/20
DB:      10.20.100.0/24, 10.20.200.0/24
```

## 비용 최적화

- 노드 수: 2대 → 1대 (50% 절감)
- NAT Gateway: Single (비용 절감)
- 작업 종료 후 클러스터 삭제

---

**관련 문서**: [오사카 Staging 클러스터 구축 보고서](../docs/오사카-Staging-클러스터-구축-보고서.md)
