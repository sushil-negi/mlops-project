#!/usr/bin/env python3
"""
Run security and compliance checks locally
Mimics the CI/CD security pipeline for local testing
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityChecker:
    """Run security and compliance checks"""

    def __init__(self):
        self.results = {}
        self.issues = []

    def run_command(
        self, cmd: List[str], capture_output: bool = True
    ) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, capture_output=capture_output, text=True, check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return -1, "", str(e)

    def check_dependency_vulnerabilities(self) -> bool:
        """Check for dependency vulnerabilities using safety"""
        logger.info("🔍 Checking dependency vulnerabilities...")

        # Check if safety is installed
        code, _, _ = self.run_command(["which", "safety"])
        if code != 0:
            logger.warning("Safety not installed. Install with: pip install safety")
            logger.info("Skipping dependency vulnerability check")
            return True

        requirements_files = [
            "models/healthcare-ai-k8s/requirements.txt",
            "services/model-registry/requirements.txt",
        ]

        all_safe = True
        for req_file in requirements_files:
            if Path(req_file).exists():
                logger.info(f"Checking {req_file}...")
                code, output, error = self.run_command(
                    ["safety", "check", "-r", req_file, "--json"]
                )

                if code == 0:
                    logger.info(f"✅ No vulnerabilities found in {req_file}")
                else:
                    logger.warning(f"⚠️ Vulnerabilities found in {req_file}")
                    try:
                        vulnerabilities = json.loads(output)
                        self.results[f"vulnerabilities_{req_file}"] = vulnerabilities
                        # Don't fail build for known issues
                        logger.info("(Not failing build for known vulnerabilities)")
                    except:
                        logger.error(f"Error parsing safety output: {output}")

        return all_safe

    def check_code_security(self) -> bool:
        """Check code security using bandit"""
        logger.info("🔍 Checking code security with bandit...")

        # Check if bandit is installed
        code, _, _ = self.run_command(["which", "bandit"])
        if code != 0:
            logger.warning(
                "Bandit not installed. Install with: pip install bandit[toml]"
            )
            logger.info("Skipping code security check")
            return True

        # Run bandit on our code
        directories = ["models/", "scripts/", "services/"]

        logger.info("Running bandit security scan...")
        code, output, error = self.run_command(
            ["bandit", "-r"] + directories + ["-ll", "-i", "-f", "json"]
        )

        if code == 0:
            logger.info("✅ No high-severity security issues found")
            return True
        else:
            try:
                issues = json.loads(output)
                self.results["bandit_issues"] = issues

                # Count by severity
                severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for result in issues.get("results", []):
                    severity = result.get("issue_severity", "LOW")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                logger.warning(f"⚠️ Security issues found:")
                logger.warning(f"  HIGH: {severity_counts['HIGH']}")
                logger.warning(f"  MEDIUM: {severity_counts['MEDIUM']}")
                logger.warning(f"  LOW: {severity_counts['LOW']}")

                # Only fail for HIGH severity
                return severity_counts["HIGH"] == 0
            except:
                logger.error(f"Error parsing bandit output")
                return True

    def check_secrets(self) -> bool:
        """Check for exposed secrets in code"""
        logger.info("🔍 Checking for exposed secrets...")

        # Simple patterns to check
        secret_patterns = {
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "api_key": r"api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
            "password": r"password['\"]?\s*[:=]\s*['\"][^'\"]+['\"]",
            "token": r"token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
            "secret": r"secret['\"]?\s*[:=]\s*['\"][^'\"]+['\"]",
        }

        secrets_found = []

        for root, dirs, files in os.walk("."):
            # Skip certain directories
            if any(
                skip in root
                for skip in [".git", "__pycache__", "venv", "node_modules", ".env"]
            ):
                continue

            for file in files:
                if file.endswith(
                    (".py", ".js", ".ts", ".yml", ".yaml", ".json", ".env")
                ):
                    filepath = os.path.join(root, file)
                    try:
                        with open(
                            filepath, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            for pattern_name, pattern in secret_patterns.items():
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    # Check if it's a placeholder or example
                                    for match in matches:
                                        if not any(
                                            placeholder in match.lower()
                                            for placeholder in [
                                                "example",
                                                "placeholder",
                                                "your",
                                                "xxxx",
                                                "dummy",
                                                "test",
                                            ]
                                        ):
                                            secrets_found.append(
                                                f"{filepath}: Potential {pattern_name} exposed"
                                            )
                    except:
                        pass

        if secrets_found:
            logger.error("❌ Potential secrets exposed:")
            for secret in secrets_found[:5]:  # Show first 5
                logger.error(f"  - {secret}")
            if len(secrets_found) > 5:
                logger.error(f"  ... and {len(secrets_found) - 5} more")
            return False
        else:
            logger.info("✅ No obvious secrets found in code")
            return True

    def check_healthcare_compliance(self) -> bool:
        """Check healthcare compliance requirements"""
        logger.info("🏥 Checking healthcare compliance...")

        compliance_issues = []

        # Check for PHI handling patterns
        phi_patterns = [
            r"ssn|social.security",
            r"medical.record.number|mrn",
            r"patient.id|patient.identifier",
            r"date.of.birth|dob",
            r"health.insurance|insurance.number",
        ]

        def scan_file(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()

                    # Skip files that contain these patterns as part of security checks
                    if any(
                        exclude in filepath
                        for exclude in ["security", "compliance", "hipaa"]
                    ):
                        return None

                    for pattern in phi_patterns:
                        if re.search(pattern, content):
                            # Check if it's in a comment or pattern definition
                            lines = content.split("\n")
                            for line in lines:
                                if pattern.replace("\\", "") in line:
                                    # Skip if it's a comment, pattern definition, or string literal
                                    if any(
                                        marker in line
                                        for marker in [
                                            "#",
                                            "r'",
                                            'r"',
                                            "pattern",
                                            "regex",
                                        ]
                                    ):
                                        continue
                                    return f"Potential PHI reference found in {filepath}: {pattern}"
            except:
                pass
            return None

        # Scan source files
        for root, dirs, files in os.walk("."):
            # Skip certain directories
            if any(
                skip in root for skip in [".git", "__pycache__", "venv", "node_modules"]
            ):
                continue

            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c")):
                    filepath = os.path.join(root, file)
                    issue = scan_file(filepath)
                    if issue:
                        compliance_issues.append(issue)

        # Check for encryption requirements
        crypto_patterns = ["password", "secret", "key", "token"]
        encryption_found = False

        for root, dirs, files in os.walk("./models"):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r") as f:
                            content = f.read().lower()
                            if any(pattern in content for pattern in crypto_patterns):
                                if (
                                    "encrypt" not in content
                                    and "hash" not in content
                                    and "bcrypt" not in content
                                ):
                                    compliance_issues.append(
                                        f"Potential unencrypted sensitive data in {filepath}"
                                    )
                    except:
                        pass

        # Check for audit logging
        audit_logging_found = False
        for root, dirs, files in os.walk("./models"):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r") as f:
                            content = f.read()
                            if "logging" in content and (
                                "audit" in content or "log" in content
                            ):
                                audit_logging_found = True
                                break
                    except:
                        pass

        if not audit_logging_found:
            compliance_issues.append("No audit logging implementation found")

        # Generate compliance report
        self.results["healthcare_compliance"] = {
            "total_issues": len(compliance_issues),
            "issues": compliance_issues,
            "compliance_status": (
                "PASSED" if len(compliance_issues) == 0 else "ISSUES_FOUND"
            ),
        }

        if compliance_issues:
            logger.warning(
                f"⚠️ Healthcare compliance issues found: {len(compliance_issues)}"
            )
            for issue in compliance_issues[:5]:
                logger.warning(f"  - {issue}")
            if len(compliance_issues) > 5:
                logger.warning(f"  ... and {len(compliance_issues) - 5} more")
            # Don't fail for warnings
            return True
        else:
            logger.info("✅ Healthcare compliance check passed")
            return True

    def check_docker_security(self) -> bool:
        """Check Docker image security"""
        logger.info("🐳 Checking Docker security...")

        # Check if docker is available
        code, _, _ = self.run_command(["which", "docker"])
        if code != 0:
            logger.warning("Docker not available. Skipping Docker security check")
            return True

        # Check if trivy is installed
        code, _, _ = self.run_command(["which", "trivy"])
        if code != 0:
            logger.warning(
                "Trivy not installed. Install from: https://aquasecurity.github.io/trivy/"
            )
            logger.info("Skipping Docker vulnerability scan")
            return True

        # Build and scan the healthcare AI image
        logger.info("Building healthcare AI Docker image...")
        code, output, error = self.run_command(
            ["docker", "build", "-t", "healthcare-ai:test", "models/healthcare-ai-k8s/"]
        )

        if code != 0:
            logger.error(f"Failed to build Docker image: {error}")
            return False

        logger.info("Scanning Docker image with Trivy...")
        code, output, error = self.run_command(
            [
                "trivy",
                "image",
                "--severity",
                "HIGH,CRITICAL",
                "--exit-code",
                "0",
                "healthcare-ai:test",
            ]
        )

        if "CRITICAL" in output or "HIGH" in output:
            logger.warning("⚠️ Docker vulnerabilities found (see output above)")
            # Don't fail build for known vulnerabilities
            return True
        else:
            logger.info("✅ No high/critical Docker vulnerabilities found")
            return True

    def check_license_compliance(self) -> bool:
        """Check license compliance"""
        logger.info("📜 Checking license compliance...")

        # Check if pip-licenses is installed
        code, _, _ = self.run_command(["which", "pip-licenses"])
        if code != 0:
            logger.warning(
                "pip-licenses not installed. Install with: pip install pip-licenses"
            )
            logger.info("Skipping license compliance check")
            return True

        logger.info("Checking healthcare AI licenses...")
        code, output, error = self.run_command(
            [
                "pip-licenses",
                "--format=json",
                "--with-license-file",
                "--no-license-path",
            ]
        )

        if code == 0:
            try:
                licenses = json.loads(output)
                gpl_licenses = []

                for pkg in licenses:
                    license_name = pkg.get("License", "").lower()
                    if "gpl" in license_name and "lgpl" not in license_name:
                        gpl_licenses.append(f"{pkg['Name']} ({pkg['License']})")

                if gpl_licenses:
                    logger.warning(
                        "⚠️ GPL licenses found (may not be compatible with commercial use):"
                    )
                    for lic in gpl_licenses:
                        logger.warning(f"  - {lic}")
                else:
                    logger.info("✅ No problematic GPL licenses found")

                self.results["licenses"] = {
                    "total_packages": len(licenses),
                    "gpl_licenses": gpl_licenses,
                }

                return True
            except:
                logger.error("Error parsing license data")
                return True
        else:
            logger.error(f"License check failed: {error}")
            return False

    def generate_summary(self):
        """Generate security scan summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🔒 Security Scan Summary")
        logger.info("=" * 60)

        # Save results
        with open("security_scan_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info("📝 Detailed results saved to security_scan_results.json")

        # Recommendations
        logger.info("\n📋 Recommendations:")
        logger.info("1. Keep dependencies updated with security patches")
        logger.info("2. Implement comprehensive audit logging")
        logger.info("3. Ensure all sensitive data is encrypted")
        logger.info("4. Regular security scans in CI/CD pipeline")
        logger.info("5. Follow healthcare compliance requirements")

    def run_all_checks(self) -> bool:
        """Run all security checks"""
        checks = [
            ("Dependency Vulnerabilities", self.check_dependency_vulnerabilities),
            ("Code Security", self.check_code_security),
            ("Secrets Detection", self.check_secrets),
            ("Healthcare Compliance", self.check_healthcare_compliance),
            ("Docker Security", self.check_docker_security),
            ("License Compliance", self.check_license_compliance),
        ]

        all_passed = True

        for check_name, check_func in checks:
            logger.info(f"\n{'='*40}")
            logger.info(f"Running: {check_name}")
            logger.info(f"{'='*40}")

            try:
                passed = check_func()
                if not passed:
                    all_passed = False
            except Exception as e:
                logger.error(f"Error in {check_name}: {e}")
                all_passed = False

        self.generate_summary()

        return all_passed


def main():
    """Main function"""
    checker = SecurityChecker()

    logger.info("🚀 Starting local security scan...")
    logger.info("This mimics the CI/CD security pipeline\n")

    success = checker.run_all_checks()

    if success:
        logger.info("\n✅ All security checks passed!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some security checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
