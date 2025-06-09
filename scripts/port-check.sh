#!/bin/bash

# Port availability checker for Healthcare AI MLOps Platform
# Checks if required ports are available before deployment

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Healthcare AI MLOps Platform - Port Availability Checker"
echo "=========================================================="

check_port() {
    local port=$1
    local service=$2
    local environment=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port ($service - $environment) is BUSY${NC}"
        echo "   Process using port: $(lsof -Pi :$port -sTCP:LISTEN | tail -n +2 | awk '{print $1, $2}')"
        return 1
    else
        echo -e "${GREEN}✅ Port $port ($service - $environment) is AVAILABLE${NC}"
        return 0
    fi
}

echo ""
echo "📋 Checking Development Environment Ports..."
echo "-------------------------------------------"

DEV_PORTS=(
    "5432:PostgreSQL:dev"
    "6379:Redis:dev"
    "9000:MinIO API:dev"
    "9001:MinIO Console:dev"
    "5050:MLflow:dev"
    "8080:Healthcare AI:dev"
    "8090:A/B Testing:dev"
    "9090:Prometheus:dev"
    "9093:Alertmanager:dev"
    "3001:Grafana:dev"
)

dev_available=0
dev_total=${#DEV_PORTS[@]}

for port_info in "${DEV_PORTS[@]}"; do
    IFS=':' read -r port service env <<< "$port_info"
    if check_port $port "$service" "$env"; then
        ((dev_available++))
    fi
done

echo ""
echo "📋 Checking Staging Environment Ports..."
echo "----------------------------------------"

STAGING_PORTS=(
    "6432:PostgreSQL:staging"
    "7379:Redis:staging"
    "10000:MinIO API:staging"
    "10001:MinIO Console:staging"
    "6050:MLflow:staging"
    "9080:Healthcare AI:staging"
    "9090:A/B Testing:staging"
    "10090:Prometheus:staging"
    "10093:Alertmanager:staging"
    "4001:Grafana:staging"
)

staging_available=0
staging_total=${#STAGING_PORTS[@]}

for port_info in "${STAGING_PORTS[@]}"; do
    IFS=':' read -r port service env <<< "$port_info"
    if check_port $port "$service" "$env"; then
        ((staging_available++))
    fi
done

echo ""
echo "📋 Checking Kubernetes NodePort Range..."
echo "---------------------------------------"

K8S_PORTS=(
    "30300:Grafana Dev:k8s-dev"
    "30500:MLflow Dev:k8s-dev"
    "30800:Healthcare AI Dev:k8s-dev"
    "30808:A/B Testing Dev:k8s-dev"
    "30900:MinIO API Dev:k8s-dev"
    "30901:MinIO Console Dev:k8s-dev"
    "30909:Prometheus Dev:k8s-dev"
    "30930:Alertmanager Dev:k8s-dev"
    "30400:Grafana Staging:k8s-staging"
    "30600:MLflow Staging:k8s-staging"
    "30900:Healthcare AI Staging:k8s-staging"
    "30908:A/B Testing Staging:k8s-staging"
    "31000:MinIO API Staging:k8s-staging"
    "31001:MinIO Console Staging:k8s-staging"
    "31009:Prometheus Staging:k8s-staging"
    "31030:Alertmanager Staging:k8s-staging"
    "30500:Grafana Production:k8s-prod"
    "30700:MLflow Production:k8s-prod"
    "31000:Healthcare AI Production:k8s-prod"
    "31008:A/B Testing Production:k8s-prod"
    "31100:MinIO API Production:k8s-prod"
    "31101:MinIO Console Production:k8s-prod"
    "31109:Prometheus Production:k8s-prod"
    "31130:Alertmanager Production:k8s-prod"
)

k8s_available=0
k8s_total=${#K8S_PORTS[@]}

for port_info in "${K8S_PORTS[@]}"; do
    IFS=':' read -r port service env <<< "$port_info"
    if check_port $port "$service" "$env"; then
        ((k8s_available++))
    fi
done

echo ""
echo "📊 Summary Report"
echo "================"
echo -e "Development Environment:   ${GREEN}$dev_available${NC}/$dev_total ports available"
echo -e "Staging Environment:       ${GREEN}$staging_available${NC}/$staging_total ports available"
echo -e "Kubernetes NodePorts:      ${GREEN}$k8s_available${NC}/$k8s_total ports available"

echo ""
if [ $dev_available -eq $dev_total ]; then
    echo -e "${GREEN}✅ Development environment ready for deployment${NC}"
else
    echo -e "${YELLOW}⚠️  Development environment has port conflicts${NC}"
fi

if [ $staging_available -eq $staging_total ]; then
    echo -e "${GREEN}✅ Staging environment ready for deployment${NC}"
else
    echo -e "${YELLOW}⚠️  Staging environment has port conflicts${NC}"
fi

if [ $k8s_available -eq $k8s_total ]; then
    echo -e "${GREEN}✅ Kubernetes environment ready for deployment${NC}"
else
    echo -e "${YELLOW}⚠️  Kubernetes environment has port conflicts${NC}"
fi

echo ""
echo "💡 Tips:"
echo "- Use './deploy.sh -a destroy -e dev' to stop development environment"
echo "- Use './deploy.sh -a destroy -e staging' to stop staging environment"
echo "- For macOS: Control Center may use port 5000 (disable AirPlay Receiver)"
echo "- For Docker: Use 'docker-compose down' to stop conflicting services"
echo "- For manual cleanup: Use 'lsof -i :<port>' to find processes using ports"

echo ""
echo "🚀 Ready to deploy?"
echo "- Development: ./deploy.sh -e dev -p docker"
echo "- Staging:     ./deploy.sh -e staging -p docker"
echo "- Kubernetes:  ./deploy.sh -e dev -p kubernetes"