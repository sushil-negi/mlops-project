#!/usr/bin/env python3
"""
Test monitoring stack integration
Verifies Prometheus, Grafana, and healthcare AI metrics
"""

import logging
import time
from typing import Any, Dict

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_service(name: str, url: str, expected_status: int = 200) -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            logger.info(f"✅ {name} is running at {url}")
            return True
        else:
            logger.error(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ {name} is not accessible: {e}")
        return False


def check_prometheus_targets() -> Dict[str, Any]:
    """Check Prometheus targets"""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets")
        data = response.json()

        active_targets = []
        down_targets = []

        for target in data["data"]["activeTargets"]:
            if target["health"] == "up":
                active_targets.append(target["labels"]["job"])
            else:
                down_targets.append(target["labels"]["job"])

        logger.info(f"📊 Active targets: {active_targets}")
        if down_targets:
            logger.warning(f"⚠️  Down targets: {down_targets}")

        return {"active": active_targets, "down": down_targets}

    except Exception as e:
        logger.error(f"Failed to check Prometheus targets: {e}")
        return {"active": [], "down": []}


def check_healthcare_metrics() -> bool:
    """Check if healthcare AI is exposing metrics"""
    try:
        # Check if healthcare AI service is running
        health_response = requests.get("http://localhost:8080/health")
        if health_response.status_code != 200:
            logger.error("Healthcare AI service is not healthy")
            return False

        # Check metrics endpoint
        metrics_response = requests.get("http://localhost:8080/metrics")
        if metrics_response.status_code == 200:
            metrics_text = metrics_response.text

            # Check for key metrics
            key_metrics = [
                "healthcare_ai_requests_total",
                "healthcare_ai_response_time_seconds",
                "healthcare_ai_model_accuracy",
                "healthcare_ai_crisis_detection_rate",
            ]

            found_metrics = []
            for metric in key_metrics:
                if metric in metrics_text:
                    found_metrics.append(metric)

            logger.info(f"✅ Found healthcare metrics: {found_metrics}")
            return len(found_metrics) > 0
        else:
            logger.error("Healthcare AI metrics endpoint not accessible")
            return False

    except Exception as e:
        logger.error(f"Failed to check healthcare metrics: {e}")
        return False


def test_grafana_datasource() -> bool:
    """Test Grafana datasource connection"""
    try:
        # Login to Grafana
        auth = ("admin", "healthcare123")

        # Check datasources
        response = requests.get("http://localhost:3001/api/datasources", auth=auth)

        if response.status_code == 200:
            datasources = response.json()
            logger.info(f"📈 Grafana datasources: {[ds['name'] for ds in datasources]}")
            return True
        else:
            logger.error(f"Failed to get Grafana datasources: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to check Grafana: {e}")
        return False


def test_alertmanager() -> bool:
    """Test Alertmanager status"""
    try:
        response = requests.get("http://localhost:9093/api/v1/status")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"🚨 Alertmanager status: {data['status']}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to check Alertmanager: {e}")
        return False


def main():
    """Run all monitoring stack tests"""
    logger.info("🔍 Testing Monitoring Stack Integration...")

    # Check core services
    services = {
        "Prometheus": "http://localhost:9090/-/healthy",
        "Grafana": "http://localhost:3001/api/health",
        "Alertmanager": "http://localhost:9093/-/healthy",
        "Healthcare AI": "http://localhost:8080/health",
        "MLflow": "http://localhost:5050/health",
    }

    all_healthy = True
    for name, url in services.items():
        if not check_service(name, url):
            all_healthy = False

    print("\n" + "=" * 50 + "\n")

    # Check Prometheus targets
    logger.info("📊 Checking Prometheus targets...")
    targets = check_prometheus_targets()

    print("\n" + "=" * 50 + "\n")

    # Check healthcare metrics
    logger.info("🏥 Checking Healthcare AI metrics...")
    healthcare_metrics_ok = check_healthcare_metrics()

    print("\n" + "=" * 50 + "\n")

    # Check Grafana
    logger.info("📈 Checking Grafana dashboards...")
    grafana_ok = test_grafana_datasource()

    print("\n" + "=" * 50 + "\n")

    # Check Alertmanager
    logger.info("🚨 Checking Alertmanager...")
    alertmanager_ok = test_alertmanager()

    print("\n" + "=" * 50 + "\n")

    # Summary
    logger.info("📋 Summary:")
    logger.info(
        f"  - Core services: {'✅ All healthy' if all_healthy else '❌ Some services down'}"
    )
    logger.info(
        f"  - Prometheus targets: {len(targets['active'])} active, {len(targets['down'])} down"
    )
    logger.info(
        f"  - Healthcare metrics: {'✅ Available' if healthcare_metrics_ok else '❌ Not available'}"
    )
    logger.info(f"  - Grafana: {'✅ Connected' if grafana_ok else '❌ Not connected'}")
    logger.info(
        f"  - Alertmanager: {'✅ Running' if alertmanager_ok else '❌ Not running'}"
    )

    # Provide Grafana URL
    if grafana_ok:
        logger.info("\n🌐 Access Grafana at: http://localhost:3001")
        logger.info("   Username: admin")
        logger.info("   Password: healthcare123")

    return all_healthy and healthcare_metrics_ok


if __name__ == "__main__":
    main()
