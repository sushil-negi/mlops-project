# Kubernetes Deployment Guide

This guide covers deploying the Healthcare AI MLOps Platform on Kubernetes, including local development with Kind and production deployment strategies.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development with Kind](#local-development-with-kind)
3. [Kubernetes Architecture](#kubernetes-architecture)
4. [Deployment Process](#deployment-process)
5. [GitOps with ArgoCD](#gitops-with-argocd)
6. [Scaling and Performance](#scaling-and-performance)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- kubectl 1.24+
- Kubernetes cluster (1.24+)
- Helm 3.0+
- Kind (for local development)
- ArgoCD CLI (optional)

### Installation

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.17.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

## Local Development with Kind

### Create Local Cluster

```bash
# Create cluster with custom configuration
kind create cluster --config infrastructure/kubernetes/kind-cluster-config.yaml
```

Kind cluster configuration:
```yaml
# infrastructure/kubernetes/kind-cluster-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
```

### Install Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

## Kubernetes Architecture

### Namespace Structure

```yaml
# infrastructure/kubernetes/mlops-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mlops-production
---
apiVersion: v1
kind: Namespace
metadata:
  name: mlops-staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: mlops-monitoring
```

### Core Components

#### Healthcare AI Deployment

```yaml
# k8s/healthcare-ai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthcare-ai
  namespace: mlops-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthcare-ai
  template:
    metadata:
      labels:
        app: healthcare-ai
    spec:
      containers:
      - name: healthcare-ai
        image: healthcare-ai:latest
        ports:
        - containerPort: 8080
        env:
        - name: MODEL_PATH
          value: "/models"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: model-storage
          mountPath: /models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-storage-pvc
```

#### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: healthcare-ai
  namespace: mlops-production
spec:
  selector:
    app: healthcare-ai
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: healthcare-ai
  namespace: mlops-production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: healthcare-ai.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: healthcare-ai
            port:
              number: 80
```

#### ConfigMaps and Secrets

```yaml
# ConfigMap for application configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: healthcare-ai-config
  namespace: mlops-production
data:
  config.yaml: |
    server:
      port: 8080
      timeout: 30s
    model:
      path: /models
      cache_size: 1000
    logging:
      level: INFO
      format: json
---
# Secret for sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: healthcare-ai-secrets
  namespace: mlops-production
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres:5432/healthcare"
  api-key: "your-api-key-here"
```

## Deployment Process

### Manual Deployment

```bash
# Create namespace
kubectl apply -f infrastructure/kubernetes/mlops-namespace.yaml

# Deploy database and storage
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/minio-deployment.yaml

# Deploy MLflow
kubectl apply -f k8s/mlflow-deployment.yaml

# Deploy Healthcare AI service
kubectl apply -f k8s/healthcare-ai-deployment.yaml

# Deploy monitoring stack
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml
```

### Helm Deployment

```bash
# Add Helm repository
helm repo add mlops https://your-org.github.io/mlops-charts
helm repo update

# Install with Helm
helm install healthcare-ai mlops/healthcare-ai \
  --namespace mlops-production \
  --values values.yaml
```

Example values.yaml:
```yaml
replicaCount: 3

image:
  repository: healthcare-ai
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
  hosts:
    - host: healthcare-ai.local
      paths: ["/"]

resources:
  limits:
    cpu: 2
    memory: 4Gi
  requests:
    cpu: 1
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## GitOps with ArgoCD

### Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Application Configuration

```yaml
# gitops/applications/healthcare-ai-production.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: healthcare-ai-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/mlops-project
    targetRevision: HEAD
    path: gitops/manifests/healthcare-ai-production
  destination:
    server: https://kubernetes.default.svc
    namespace: mlops-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### Directory Structure for GitOps

```
gitops/
├── applications/
│   ├── healthcare-ai-production.yaml
│   └── healthcare-ai-staging.yaml
└── manifests/
    ├── healthcare-ai-production/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── ingress.yaml
    └── healthcare-ai-staging/
        ├── deployment.yaml
        ├── service.yaml
        ├── configmap.yaml
        └── ingress.yaml
```

## Scaling and Performance

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: healthcare-ai-hpa
  namespace: mlops-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthcare-ai
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaling

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: healthcare-ai-vpa
  namespace: mlops-production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthcare-ai
  updatePolicy:
    updateMode: "Auto"
```

### Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mlops-production-quota
  namespace: mlops-production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    persistentvolumeclaims: "10"
```

## Monitoring and Observability

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: healthcare-ai
  namespace: mlops-monitoring
spec:
  selector:
    matchLabels:
      app: healthcare-ai
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboard

Deploy pre-configured dashboards:
```bash
kubectl create configmap grafana-dashboards \
  --from-file=dashboards/ \
  -n mlops-monitoring
```

### Logging with Fluentd

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: mlops-monitoring
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      <parse>
        @type json
      </parse>
    </source>
    
    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>
    
    <match **>
      @type elasticsearch
      host elasticsearch.mlops-monitoring.svc.cluster.local
      port 9200
      logstash_format true
    </match>
```

## Troubleshooting

### Common Issues

#### 1. Pod Not Starting

```bash
# Check pod status
kubectl get pods -n mlops-production
kubectl describe pod <pod-name> -n mlops-production

# Check logs
kubectl logs <pod-name> -n mlops-production
kubectl logs <pod-name> -n mlops-production --previous
```

#### 2. Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n mlops-production
kubectl get svc -n mlops-production

# Test service connectivity
kubectl run test-pod --image=busybox -it --rm -- wget -qO- http://healthcare-ai.mlops-production.svc.cluster.local/health
```

#### 3. Storage Issues

```bash
# Check PVC status
kubectl get pvc -n mlops-production
kubectl describe pvc <pvc-name> -n mlops-production

# Check storage class
kubectl get storageclass
```

### Debugging Commands

```bash
# Execute commands in pod
kubectl exec -it <pod-name> -n mlops-production -- /bin/bash

# Port forward for local access
kubectl port-forward svc/healthcare-ai -n mlops-production 8080:80

# Get pod metrics
kubectl top pods -n mlops-production
kubectl top nodes

# Check events
kubectl get events -n mlops-production --sort-by='.lastTimestamp'
```

### Performance Debugging

```bash
# CPU and memory usage
kubectl top pod <pod-name> -n mlops-production --containers

# Network policies
kubectl get networkpolicies -n mlops-production

# Check resource limits
kubectl describe pod <pod-name> -n mlops-production | grep -A 5 "Limits\|Requests"
```

## Best Practices

### Security

1. **Use Network Policies**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: healthcare-ai-netpol
   spec:
     podSelector:
       matchLabels:
         app: healthcare-ai
     policyTypes:
     - Ingress
     - Egress
   ```

2. **Pod Security Standards**:
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: mlops-production
     labels:
       pod-security.kubernetes.io/enforce: restricted
   ```

3. **RBAC Configuration**:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: healthcare-ai-role
   rules:
   - apiGroups: [""]
     resources: ["configmaps", "secrets"]
     verbs: ["get", "list", "watch"]
   ```

### High Availability

1. **Pod Disruption Budgets**:
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: healthcare-ai-pdb
   spec:
     minAvailable: 2
     selector:
       matchLabels:
         app: healthcare-ai
   ```

2. **Anti-affinity Rules**:
   ```yaml
   affinity:
     podAntiAffinity:
       requiredDuringSchedulingIgnoredDuringExecution:
       - labelSelector:
           matchExpressions:
           - key: app
             operator: In
             values:
             - healthcare-ai
         topologyKey: kubernetes.io/hostname
   ```

## Next Steps

- [Production Deployment](./production.md) - Production-specific considerations
- [Monitoring Setup](../monitoring/kubernetes.md) - Kubernetes monitoring details
- [CI/CD Integration](../development/cicd.md) - Automated deployments