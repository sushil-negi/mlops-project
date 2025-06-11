# Contributing to Healthcare AI MLOps Platform

Thank you for your interest in contributing to the Healthcare AI MLOps Platform! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Code Standards](#code-standards)
4. [Contribution Process](#contribution-process)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Issue Reporting](#issue-reporting)
8. [Pull Request Guidelines](#pull-request-guidelines)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Kubernetes (kind or minikube for local development)
- Git

### Setting Up Your Development Environment

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mlops-project.git
   cd mlops-project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Run the development setup script:
   ```bash
   ./scripts/setup-dev.sh
   ```

## Code Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable and function names

Example:
```python
from typing import List, Dict, Optional

def process_healthcare_data(
    data: List[Dict[str, Any]], 
    validate: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Process healthcare data with optional validation.
    
    Args:
        data: List of healthcare records
        validate: Whether to validate input data
        
    Returns:
        Processed data dictionary or None if validation fails
    """
    # Implementation here
    pass
```

### Docker Best Practices

- Use multi-stage builds to minimize image size
- Pin dependency versions
- Run containers as non-root user
- Use .dockerignore to exclude unnecessary files

### Kubernetes Manifests

- Use semantic versioning for container images
- Include resource limits and requests
- Add appropriate labels and annotations
- Use ConfigMaps and Secrets for configuration

## Contribution Process

1. **Check existing issues** - Look for related issues or feature requests
2. **Create an issue** - If none exists, create one describing your proposed change
3. **Fork and branch** - Create a feature branch from `main`
4. **Develop** - Make your changes following code standards
5. **Test** - Ensure all tests pass and add new tests as needed
6. **Document** - Update documentation for your changes
7. **Submit PR** - Create a pull request with a clear description

### Branch Naming Convention

- Feature: `feature/description-of-feature`
- Bug fix: `fix/description-of-fix`
- Documentation: `docs/description-of-change`
- Refactoring: `refactor/description-of-refactor`

## Testing Requirements

### Unit Tests

All new code must include unit tests. Place tests in the `tests/unit/` directory.

```python
import pytest
from models.healthcare_ai.src.healthcare_ai_engine import HealthcareAIEngine

def test_healthcare_classification():
    engine = HealthcareAIEngine()
    result = engine.classify_query("I need help with medication")
    assert result['category'] in ['medication', 'prescription']
```

### Integration Tests

For features that interact with external services, add integration tests in `tests/integration/`.

### End-to-End Tests

For user-facing features, add E2E tests in `tests/e2e/`.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=models --cov=scripts --cov-report=html
```

## Documentation

### Code Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style docstrings
- Include examples for complex functions

### Project Documentation

- Update relevant documentation in the `docs/` directory
- Add entries to CHANGELOG.md for notable changes
- Update README.md if adding new features or changing setup

### API Documentation

- Document all API endpoints with request/response examples
- Include error response documentation
- Update OpenAPI/Swagger specs if applicable

## Issue Reporting

When reporting issues, please include:

1. **Description** - Clear description of the issue
2. **Reproduction steps** - How to reproduce the issue
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment** - OS, Python version, Docker version, etc.
6. **Logs** - Relevant error messages or logs

Use issue templates when available.

## Pull Request Guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No new warnings
```

### Review Process

1. All PRs require at least one review
2. Address all review comments
3. Keep PRs focused and small when possible
4. Ensure CI/CD checks pass

### Commit Messages

Follow conventional commit format:

```
type(scope): subject

body

footer
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(model): add healthcare data validation

- Add input validation for patient data
- Implement data sanitization
- Add unit tests for validation logic

Closes #123
```

## Additional Resources

- [Project Architecture](../project/architecture.md)
- [Testing Strategy](./testing-strategy.md)
- [Deployment Guide](../deployment/production.md)
- [API Reference](../api/reference.md)

## Questions?

If you have questions, feel free to:
- Open a discussion in GitHub Discussions
- Ask in project chat/Slack channel
- Email the maintainers

Thank you for contributing to making healthcare AI more accessible and reliable!