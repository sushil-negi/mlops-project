#!/usr/bin/env python3
"""Test monitoring stack integration with healthcare AI service"""

import json
import time

import requests


def test_prometheus_targets():
    """Check if Prometheus is scraping targets"""
    print("Testing Prometheus targets...")
    try:
        response = requests.get("http://localhost:9090/api/v1/targets")
        data = response.json()

        active_targets = [
            t for t in data["data"]["activeTargets"] if t["health"] == "up"
        ]
        print(f"✓ Prometheus has {len(active_targets)} healthy targets")

        for target in active_targets[:3]:
            print(
                f"  - {target['labels'].get('job', 'unknown')}: {target['scrapeUrl']}"
            )

        return True
    except Exception as e:
        print(f"✗ Failed to check Prometheus targets: {e}")
        return False


def test_grafana_health():
    """Check if Grafana is accessible"""
    print("\nTesting Grafana health...")
    try:
        response = requests.get("http://localhost:3001/api/health")
        if response.status_code == 200:
            print("✓ Grafana is healthy")
            return True
        else:
            print(f"✗ Grafana returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to check Grafana: {e}")
        return False


def test_alertmanager():
    """Check if Alertmanager is running"""
    print("\nTesting Alertmanager...")
    try:
        response = requests.get("http://localhost:9093/api/v2/status")
        data = response.json()
        print(f"✓ Alertmanager is running (uptime: {data['uptime']})")
        return True
    except Exception as e:
        print(f"✗ Failed to check Alertmanager: {e}")
        return False


def test_healthcare_metrics():
    """Generate some test metrics from healthcare AI"""
    print("\nGenerating test healthcare metrics...")
    try:
        # Make a few test requests to generate metrics
        test_queries = [
            {"query": "I need help with anxiety"},
            {"query": "What are symptoms of depression?"},
            {"query": "I'm having thoughts of self-harm"},  # Crisis query
        ]

        for query in test_queries:
            response = requests.post(
                "http://localhost:8889/query",
                json=query,
                headers={"Content-Type": "application/json"},
            )
            print(
                f"  - Query: '{query['query'][:30]}...' -> Status: {response.status_code}"
            )
            time.sleep(0.5)

        return True
    except Exception as e:
        print(f"✗ Failed to generate test metrics: {e}")
        return False


def check_metrics_in_prometheus():
    """Check if healthcare metrics appear in Prometheus"""
    print("\nChecking healthcare metrics in Prometheus...")
    try:
        # Check for healthcare-specific metrics
        metrics_to_check = [
            "healthcare_ai_requests_total",
            "healthcare_ai_response_time_seconds",
            "healthcare_ai_crisis_detections_total",
        ]

        found_metrics = []
        response = requests.get("http://localhost:9090/api/v1/label/__name__/values")
        available_metrics = response.json()["data"]

        for metric in metrics_to_check:
            if metric in available_metrics:
                found_metrics.append(metric)

        if found_metrics:
            print(f"✓ Found {len(found_metrics)} healthcare metrics in Prometheus:")
            for metric in found_metrics:
                print(f"  - {metric}")
        else:
            print("✗ No healthcare metrics found in Prometheus yet")
            print("  (This might be normal if the metrics exporter needs more time)")

        return len(found_metrics) > 0
    except Exception as e:
        print(f"✗ Failed to check metrics: {e}")
        return False


def main():
    """Run all monitoring integration tests"""
    print("=== Healthcare AI Monitoring Stack Integration Test ===\n")

    tests = [
        test_prometheus_targets,
        test_grafana_health,
        test_alertmanager,
        test_healthcare_metrics,
        check_metrics_in_prometheus,
    ]

    results = []
    for test in tests:
        results.append(test())
        time.sleep(1)

    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} tests")

    if passed == total:
        print("\n✓ All monitoring components are working!")
        print("\nAccess the monitoring stack at:")
        print("  - Prometheus: http://localhost:9090")
        print("  - Grafana: http://localhost:3001 (admin/healthcare123)")
        print("  - Alertmanager: http://localhost:9093")
    else:
        print("\n⚠️  Some components need attention")

    return passed == total


if __name__ == "__main__":
    exit(0 if main() else 1)
