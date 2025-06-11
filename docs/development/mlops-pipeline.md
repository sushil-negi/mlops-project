# MLOps Pipeline Guide

This document explains when and how to use the different CI/CD pipelines in this healthcare AI MLOps platform.

## Pipeline Overview

Our MLOps platform uses three distinct pipelines, each optimized for different purposes and run frequencies:

### 🔄 CI Pipeline
**Purpose:** Fast feedback on code quality and basic functionality  
**File:** `.github/workflows/ci.yml`

### 🤖 ML Pipeline  
**Purpose:** Model training, validation, and healthcare-specific testing  
**File:** `.github/workflows/ml-pipeline.yml`

### 🛡️ Security Pipeline
**Purpose:** Comprehensive security scanning and compliance validation  
**File:** `.github/workflows/security-scan.yml`

---

## When to Use Each Pipeline

### **CI Pipeline** - Every Code Change
**Triggers:**
- ✅ Every push to any branch
- ✅ Every pull request
- ✅ Manual dispatch (`workflow_dispatch`)

**What it validates:**
- Data quality validation (duplicate detection, format checks)
- Response quality metrics (empathy ≥65%, clarity, completeness, safety)
- Code formatting (import sorting with isort)
- Basic healthcare AI functionality tests

**Expected Runtime:** 2-5 minutes

**Use this when:**
- Making any code changes
- Creating pull requests
- Quick validation before merging

---

### **ML Pipeline** - Model Changes & Training
**Triggers:**
- ✅ Changes to training data (`data/` directory)
- ✅ Model code modifications (`models/`, `scripts/train_*`)
- ✅ Scheduled retraining (weekly/monthly)
- ✅ Manual dispatch for experiments

**What it validates:**
- Model training and validation accuracy
- Healthcare category coverage (11 categories)
- Crisis detection accuracy (must be 100%)
- Model performance metrics
- Model artifact management with MLflow

**Expected Runtime:** 10-30 minutes (depending on dataset size)

**Use this when:**
- Adding new training data
- Modifying model architecture
- Updating healthcare categories
- Scheduled model retraining
- Experimenting with new features

---

### **Security Pipeline** - Regular Security Audits
**Triggers:**
- ✅ **Daily scheduled** (3 AM UTC)
- ✅ Push to `main` branch (production deployments)
- ✅ Pull requests to `main` branch
- ✅ Manual dispatch for security reviews

**What it scans:**
- **Dependency vulnerabilities** (safety, pip-audit)
- **Code security** (bandit, semgrep)
- **Secrets detection** (pattern-based scanning)
- **Docker image security** (trivy, grype)
- **Healthcare compliance** (PHI pattern detection)
- **License compliance** (GPL license detection)

**Expected Runtime:** 5-15 minutes

**Use this when:**
- Deploying to production (`main` branch)
- Adding new dependencies
- Security reviews and audits
- Compliance validation

---

## Pipeline Run Patterns

### **Daily Development Flow**
```
Developer commits code
├── CI Pipeline (every commit) ────────── Fast feedback loop
├── ML Pipeline (if data/model changed) ── Thorough validation
└── Security Pipeline (if main branch) ─── Production security
```

### **Scheduled Operations**
```
Daily (3 AM UTC)
└── Security Pipeline ──── Comprehensive security audit

Weekly/Monthly
└── ML Pipeline ──── Scheduled model retraining
```

---

## Error Handling & Resilience

### **CI Pipeline**
- ❌ **Fails fast** on quality issues (blocks merges)
- ✅ Must pass for pull request approval

### **ML Pipeline**  
- ⚠️ **Warns on accuracy issues** but allows manual review
- ✅ Generates detailed validation reports

### **Security Pipeline**
- ✅ **Never blocks development** (`continue-on-error: true`)
- 📊 Generates comprehensive security reports
- 🚨 Alerts security team on critical issues (Slack integration)

---

## Local Testing

Before pushing code, you can run pipeline validations locally:

### **CI Pipeline Testing**
```bash
# Data quality validation
python3 scripts/data_quality_checks.py

# Response quality validation  
python3 tests/response_quality_validation.py

# Import sorting
python3 -m isort --check-only --diff .
```

### **ML Pipeline Testing**
```bash
# Model validation
python3 tests/healthcare_model_validation.py

# Crisis detection validation
python3 tests/crisis_detection_validation.py
```

### **Security Pipeline Testing**
```bash
# Comprehensive security scan
python3 scripts/run_security_checks.py
```

---

## Pipeline Artifacts

Each pipeline generates specific artifacts for review:

### **CI Pipeline Artifacts**
- `data_quality_report.json` - Data validation results
- `response_quality_validation_report.json` - Response metrics

### **ML Pipeline Artifacts**  
- `healthcare_validation_report.json` - Model performance
- `crisis_detection_validation_report.json` - Crisis handling validation
- MLflow artifacts and metrics

### **Security Pipeline Artifacts**
- `vulnerability-reports/` - Dependency scan results
- `security-scan-results/` - Code security analysis
- `compliance-report/` - Healthcare compliance status
- `security-summary.md` - Executive summary

---

## Best Practices

### **Development Workflow**
1. 🔄 **Run CI locally** before pushing
2. 🤖 **Test ML changes** with validation scripts
3. 🛡️ **Review security reports** for main branch changes
4. 📊 **Monitor pipeline results** in GitHub Actions

### **Performance Optimization**
- **CI Pipeline:** Keep fast (< 5 min) for developer productivity
- **ML Pipeline:** Can be slower but should provide detailed feedback  
- **Security Pipeline:** Comprehensive but non-blocking

### **Troubleshooting**
- **CI failures:** Usually data quality or formatting issues
- **ML failures:** Often accuracy thresholds or missing categories
- **Security warnings:** Review but don't block development

---

## Healthcare AI Specific Validations

### **Crisis Detection Requirements**
- ✅ 100% accuracy on crisis query detection
- ✅ Emergency resource information (988, 911, crisis hotlines)
- ✅ Urgent response indicators
- ✅ <10% false positive rate

### **Healthcare Compliance**
- ✅ PHI pattern detection and prevention
- ✅ Medical disclaimer requirements  
- ✅ HIPAA compliance checks
- ✅ Audit logging validation

### **Response Quality Standards**
- ✅ Empathy score ≥ 65%
- ✅ Clarity and completeness metrics
- ✅ Safety and appropriateness validation
- ✅ Healthcare category coverage

---

## Pipeline Configuration

All pipeline configurations are version-controlled in `.github/workflows/`:

- `ci.yml` - CI Pipeline configuration
- `ml-pipeline.yml` - ML Pipeline configuration  
- `security-scan.yml` - Security Pipeline configuration

Pipeline parameters can be adjusted in these files, including:
- Trigger conditions
- Validation thresholds
- Artifact retention
- Notification settings

---

For questions or pipeline improvements, please create an issue or contact the MLOps team.