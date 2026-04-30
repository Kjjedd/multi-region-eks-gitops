# AWS Transit Gateway 멀티 리전 연결 가이드

> 3개 리전 EKS 클러스터를 TGW Peering으로 연결

## 아키텍처

```
        서울 Hub (192.168.0.0/16)
        TGW: seoul-hub-tgw
              /          \
    TGW Peering      TGW Peering
          /                \
도쿄 DR              오사카 Staging
10.30.0.0/16         10.20.0.0/16
tokyo-peer-tgw       osaka-peer-tgw
```

## 네트워크 구성

| 리전 | VPC CIDR | TGW ASN | 역할 |
|------|----------|---------|------|
| 서울 | 192.168.0.0/16 | 64512 | Prod + Hub |
| 오사카 | 10.20.0.0/16 | 64514 | Staging |
| 도쿄 | 10.30.0.0/16 | 64513 | DR |

## 구축 절차

## 구축 절차

### 1. TGW 생성 및 VPC Attachment

각 리전에서 TGW 생성 후 Private Subnet에 Attachment 생성

### 2. TGW Peering 연결

**서울에서 Peering 요청**:
```
Transit Gateway Attachments → Create
- Type: Peering Connection
- Account: Another account
- Account ID: <대상 계정 ID>
- Region: <대상 리전>
- Transit Gateway (accepter): <대상 TGW ID>
```

**대상 리전에서 승인**:
```
Transit Gateway Attachments → Actions → Accept
```

### 3. Route Table 설정

**TGW Route Table**:
```bash
# 서울 TGW Route Table
10.30.0.0/16 → seoul-tokyo-peering
10.20.0.0/16 → seoul-osaka-peering

# 도쿄 TGW Route Table
192.168.0.0/16 → tokyo-seoul-peering

# 오사카 TGW Route Table
192.168.0.0/16 → osaka-seoul-peering
```

**VPC Route Table** (Private Subnet):
```bash
# 서울 VPC
10.30.0.0/16 → seoul-hub-tgw
10.20.0.0/16 → seoul-hub-tgw

# 도쿄 VPC
192.168.0.0/16 → tokyo-peer-tgw

# 오사카 VPC
192.168.0.0/16 → osaka-peer-tgw
```

### 4. Security Group 설정

**각 클러스터의 ClusterSharedNodeSecurityGroup에 추가**:

```bash
# 서울
Type: All traffic, Source: 10.30.0.0/16 (도쿄)
Type: All traffic, Source: 10.20.0.0/16 (오사카)

# 도쿄
Type: All traffic, Source: 192.168.0.0/16 (서울)

# 오사카
Type: All traffic, Source: 192.168.0.0/16 (서울)
```

## 연결 테스트

```bash
# 노드 IP 확인
kubectl get nodes -o wide

# 테스트 Pod 생성
kubectl run -it --rm ping-test --image=busybox --restart=Never -- sh

# HTTP 테스트 (권장)
curl http://<대상-노드-IP>:8000/healthz
```

## ArgoCD 멀티 클러스터 연동

### 1. Cross-account IAM 설정

```bash
eksctl create iamidentitymapping \
  --cluster <자기클러스터> \
  --region <자기리전> \
  --arn arn:aws:iam::816040392320:user/<서울IAM유저> \
  --username teamA \
  --group system:masters
```

### 2. kubeconfig 연동

```bash
aws eks update-kubeconfig --region ap-northeast-1 --name tokyo-dr-eks
aws eks update-kubeconfig --region ap-northeast-3 --name osaka-staging-eks
```

### 3. ArgoCD 클러스터 등록

```bash
argocd cluster add <도쿄-context> --name tokyo-dr-eks
argocd cluster add <오사카-context> --name osaka-staging-eks
```

## 트러블슈팅

### Ping 실패

**체크리스트**:
1. TGW Route Table 경로 확인
2. VPC Route Table 경로 확인
3. Security Group 인바운드 규칙 확인
4. ICMP 허용 여부 확인 (또는 HTTP 테스트 사용)

### 노드가 Public Subnet에 배치

**해결**: `--node-private-networking` 플래그 사용 또는 Public Subnet Route Table에도 TGW 경로 추가

### Cross-account 접근 불가

**해결**: Cross-account IAM Role 생성 + assume-role 사용

```bash
aws eks update-kubeconfig \
  --region ap-northeast-3 \
  --name osaka-staging-eks \
  --role-arn arn:aws:iam::<대상계정ID>:role/TeamA-EKS-Access
```

---

## 참고 자료

- [AWS Transit Gateway 공식 문서](https://docs.aws.amazon.com/vpc/latest/tgw/)
- [Transit Gateway Peering](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-peering.html)
- [EKS Networking Best Practices](https://aws.github.io/aws-eks-best-practices/networking/)
