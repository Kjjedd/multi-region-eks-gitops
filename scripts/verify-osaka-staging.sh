#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_NAME="${CLUSTER_NAME_OVERRIDE:-$(awk '/^  name: /{print $2; exit}' "${ROOT_DIR}/infra/eksctl/cluster-c-osaka-staging.yaml")}"
REGION="ap-northeast-3"
EXPECTED_ACCOUNT="165749212250"

echo "[1/6] AWS caller identity"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ARN="$(aws sts get-caller-identity --query Arn --output text)"
echo "  account: ${ACCOUNT_ID}"
echo "  arn: ${ARN}"

if [[ "${ACCOUNT_ID}" != "${EXPECTED_ACCOUNT}" ]]; then
  echo "Expected account ${EXPECTED_ACCOUNT}, got ${ACCOUNT_ID}" >&2
  exit 1
fi

echo "[2/6] Tool versions"
aws --version
kubectl version --client
eksctl version

echo "[3/6] Kustomize render"
kubectl kustomize "${ROOT_DIR}/gitops/overlays/cluster-c" >/tmp/cluster-c-rendered.yaml
echo "  rendered: /tmp/cluster-c-rendered.yaml"

echo "[4/6] Cluster config preview"
test -f "${ROOT_DIR}/infra/eksctl/cluster-c-osaka-staging.yaml"
echo "  found: ${ROOT_DIR}/infra/eksctl/cluster-c-osaka-staging.yaml"
echo "  target cluster name: ${CLUSTER_NAME}"

echo "[5/6] Current kubectl context"
kubectl config current-context || true

echo "[6/6] Suggested next commands"
cat <<EOF
eksctl create cluster -f ${ROOT_DIR}/infra/eksctl/cluster-c-osaka-staging.yaml
aws eks update-kubeconfig --region ${REGION} --name ${CLUSTER_NAME}
kubectl get nodes
kubectl apply -k ${ROOT_DIR}/gitops/overlays/cluster-c
EOF
