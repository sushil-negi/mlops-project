# Production Deployment Guide

This guide covers best practices, security considerations, and operational procedures for deploying the Healthcare AI MLOps Platform in production environments.

## Table of Contents

1. [Production Requirements](#production-requirements)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Security Hardening](#security-hardening)
4. [Deployment Strategy](#deployment-strategy)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
7. [Performance Optimization](#performance-optimization)
8. [Operational Procedures](#operational-procedures)
9. [Compliance and Auditing](#compliance-and-auditing)

## Production Requirements

### Infrastructure Requirements

#### Compute Resources
- **Kubernetes Cluster**: 3+ master nodes, 5+ worker nodes
- **CPU**: Minimum 8 cores per node
- **Memory**: Minimum 32GB RAM per node
- **Storage**: SSD-backed storage with 500+ IOPS

#### Network Requirements
- **Load Balancer**: Layer 7 with SSL termination
- **CDN**: For static assets and model artifacts
- **VPN**: For secure administrative access
- **Firewall**: Web Application Firewall (WAF)

#### High Availability
- Multi-AZ deployment
- Minimum 3 replicas for stateless services
- Database replication with automatic failover
- Geographic redundancy for critical data

### Software Requirements

```yaml
# Minimum versions for production
kubernetes: "1.24+"
docker: "20.10+"
helm: "3.10+"
prometheus: "2.37+"
grafana: "9.0+"
postgresql: "14+"
redis: "7.0+"
```

## Infrastructure Setup

### Cloud Provider Configuration

#### AWS Example

```terraform
# terraform/aws/production.tf
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "mlops-production"
  cluster_version = "1.27"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    general = {
      min_size     = 3
      max_size     = 10
      desired_size = 5
      
      instance_types = ["t3.xlarge"]
      
      k8s_labels = {
        Environment = "production"
        NodeType    = "general"
      }
    }
    
    ml = {
      min_size     = 2
      max_size     = 6
      desired_size = 3
      
      instance_types = ["g4dn.xlarge"]
      
      taints = [{
        key    = "workload"
        value  = "ml"
        effect = "NO_SCHEDULE"
      }]
      
      k8s_labels = {
        Environment = "production"
        NodeType    = "ml"
      }
    }
  }
}
```

### Database Setup

#### PostgreSQL High Availability

```yaml
# postgresql-ha.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: mlops-production
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "16MB"
      maintenance_work_mem: "256MB"
      
  bootstrap:
    initdb:
      database: mlops
      owner: mlops
      secret:
        name: postgres-credentials
        
  storage:
    size: 100Gi
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
    
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: "s3://mlops-backups/postgres"
      s3Credentials:
        accessKeyId:
          name: backup-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-credentials
          key: SECRET_ACCESS_KEY
```

### Object Storage Configuration

```yaml
# minio-production.yaml
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: minio-production
  namespace: mlops-production
spec:
  servers: 4
  volumesPerServer: 4
  mountPath: /data
  
  pools:
  - servers: 4
    volumesPerServer: 4
    volumeClaimTemplate:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 1Ti
        storageClassName: fast-ssd
        
  features:
    bucketDNS: true
    
  certConfig:
    commonName: "*.minio.production.local"
    organizationName: ["MLOps"]
    dnsNames:
    - "minio.production.local"
    
  env:
  - name: MINIO_PROMETHEUS_AUTH_TYPE
    value: "public"
```

## Security Hardening

### Network Security

#### Network Policies

```yaml
# network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: healthcare-ai-network-policy
  namespace: mlops-production
spec:
  podSelector:
    matchLabels:
      app: healthcare-ai
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: mlops-production
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: mlops-production
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 9000  # MinIO
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53
```

### Pod Security

#### Security Contexts

```yaml
# deployment-secure.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthcare-ai
  namespace: mlops-production
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: healthcare-ai
        image: healthcare-ai:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

### Secrets Management

#### Using Sealed Secrets

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Create sealed secret
echo -n mypassword | kubectl create secret generic db-password \
  --dry-run=client \
  --from-file=password=/dev/stdin \
  -o yaml | kubeseal -o yaml > sealed-secret.yaml
```

#### External Secrets Operator

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: mlops-production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-credentials
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: mlops/database
      property: username
  - secretKey: password
    remoteRef:
      key: mlops/database
      property: password
```

## Deployment Strategy

### Blue-Green Deployment

```yaml
# blue-green-deployment.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: healthcare-ai
  namespace: mlops-production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthcare-ai
  progressDeadlineSeconds: 60
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 30s
    webhooks:
    - name: load-test
      url: http://flagger-loadtester.mlops-production/
      timeout: 5s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://healthcare-ai.mlops-production/"
```

### Rolling Update Strategy

```yaml
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  minReadySeconds: 30
  progressDeadlineSeconds: 600
```

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: healthcare-ai-alerts
  namespace: mlops-monitoring
spec:
  groups:
  - name: healthcare-ai
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{job="healthcare-ai",status=~"5.."}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"
        
    - alert: HighLatency
      expr: histogram_quantile(0.95, http_request_duration_seconds_bucket{job="healthcare-ai"}) > 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected"
        description: "95th percentile latency is {{ $value }}s"
        
    - alert: PodMemoryUsage
      expr: container_memory_usage_bytes{pod=~"healthcare-ai-.*"} / container_spec_memory_limit_bytes > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage"
        description: "Pod {{ $labels.pod }} memory usage is above 90%"
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Healthcare AI Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{job='healthcare-ai'}[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{job='healthcare-ai',status=~'5..'}[5m]) / rate(http_requests_total{job='healthcare-ai'}[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job='healthcare-ai'}[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Backup and Disaster Recovery

### Backup Strategy

```yaml
# velero-backup.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  template:
    ttl: 720h  # 30 days retention
    includedNamespaces:
    - mlops-production
    - mlops-monitoring
    labelSelector:
      matchLabels:
        backup: "true"
    snapshotVolumes: true
    volumeSnapshotLocations:
    - aws-default
    storageLocation: aws-default
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour

#### Recovery Procedures

```bash
# 1. Restore from backup
velero restore create --from-backup daily-backup-20240101

# 2. Verify database integrity
kubectl exec -it postgres-0 -n mlops-production -- psql -U mlops -c "SELECT COUNT(*) FROM models;"

# 3. Verify application health
kubectl get pods -n mlops-production
curl -f http://healthcare-ai.production.com/health

# 4. Switch DNS if needed
# Update Route53/CloudFlare to point to recovered cluster
```

## Performance Optimization

### Resource Optimization

```yaml
# vpa-recommendation.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: healthcare-ai-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthcare-ai
  updatePolicy:
    updateMode: "Off"  # Recommendation only
  resourcePolicy:
    containerPolicies:
    - containerName: healthcare-ai
      maxAllowed:
        cpu: 4
        memory: 8Gi
```

### Caching Strategy

```yaml
# redis-production.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  serviceName: redis-cluster
  replicas: 6
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server"]
        args:
        - /conf/redis.conf
        - --cluster-enabled yes
        - --cluster-config-file nodes.conf
        - --cluster-node-timeout 5000
        - --appendonly yes
        - --maxmemory 2gb
        - --maxmemory-policy allkeys-lru
```

## Operational Procedures

### Deployment Checklist

- [ ] Run automated tests
- [ ] Review security scan results
- [ ] Update change log
- [ ] Notify stakeholders
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Monitor metrics for 30 minutes
- [ ] Deploy to production (canary)
- [ ] Monitor canary metrics
- [ ] Complete rollout
- [ ] Update documentation

### Incident Response

```yaml
# runbook.yaml
name: Healthcare AI Service Down
severity: Critical
escalation:
  - oncall-engineer
  - platform-lead
  - cto

steps:
  1. Check service health:
     kubectl get pods -n mlops-production
     kubectl logs -l app=healthcare-ai -n mlops-production
     
  2. Check dependencies:
     kubectl get pods -n mlops-production | grep -E "(postgres|redis|minio)"
     
  3. Review recent changes:
     kubectl rollout history deployment/healthcare-ai -n mlops-production
     
  4. Rollback if needed:
     kubectl rollout undo deployment/healthcare-ai -n mlops-production
     
  5. Scale up if resource issue:
     kubectl scale deployment/healthcare-ai --replicas=10 -n mlops-production
```

## Compliance and Auditing

### Audit Logging

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    namespaces: ["mlops-production"]
    verbs: ["create", "update", "patch", "delete"]
    resources:
    - group: ""
      resources: ["secrets", "configmaps"]
    - group: "apps"
      resources: ["deployments", "replicasets"]
```

### Compliance Checks

```bash
# CIS Kubernetes Benchmark
kube-bench run --targets node,master,etcd,policies

# Security scanning
trivy image healthcare-ai:latest
kubesec scan deployment.yaml

# Network policy validation
kubectl describe networkpolicies -n mlops-production
```

### Data Privacy

```yaml
# pii-protection.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: privacy-config
data:
  rules.yaml: |
    pii_fields:
      - email
      - phone
      - ssn
      - credit_card
    encryption:
      algorithm: AES-256-GCM
      key_rotation: 90d
    retention:
      logs: 30d
      metrics: 90d
      traces: 7d
```

## Production Readiness Checklist

### Infrastructure
- [ ] Multi-AZ deployment configured
- [ ] Auto-scaling policies in place
- [ ] Backup and recovery tested
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup

### Security
- [ ] Network policies implemented
- [ ] Secrets management configured
- [ ] RBAC policies defined
- [ ] Security scanning automated
- [ ] Compliance requirements met

### Operations
- [ ] Runbooks documented
- [ ] On-call rotation established
- [ ] SLOs defined and monitored
- [ ] Change management process
- [ ] Incident response plan

### Performance
- [ ] Load testing completed
- [ ] Resource limits optimized
- [ ] Caching strategy implemented
- [ ] CDN configured
- [ ] Database indexes optimized

## Next Steps

- [Monitoring Guide](../monitoring/production.md) - Production monitoring setup
- [Security Guide](../security/production.md) - Security best practices
- [Troubleshooting Guide](../troubleshooting/production.md) - Common issues and solutions