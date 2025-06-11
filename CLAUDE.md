# Claude Instructions

## Commit Message Guidelines

- No marketing language in commit messages
- No Anthropic or Claude marketing/branding
- Keep commit messages concise and descriptive - one line only
- Focus on what was changed, not promotional language
- Example: "Fix code formatting and CI/CD compliance across all MLOps services" (good)
- Avoid: Marketing terms, emojis, promotional language, or AI tool branding (bad)

## Code Quality

- Run Black formatting before commits
- Check flake8 compliance  
- Run full test suite before committing
- Use pre-commit hooks when available

## MLOps Platform Development

- Model Registry 2.0: Universal model management with lineage tracking
- Pipeline Orchestrator 2.0: DAG-based workflow engine for ML pipelines
- Feature Store 2.0: Real-time feature management platform
- Focus on enterprise-grade MLOps capabilities

## Testing Requirements - Core Principle

- ALL CI/ML pipeline tests must pass before committing
- Run complete test suite until clean run achieved:
  - Black code formatting
  - isort import sorting
  - mypy type checking
  - End-to-end tests
  - Integration tests
  - Service architecture validation
- No commits allowed until 100% test pass rate
- 47 unit/integration tests currently passing
- Experiment Tracking 2.0: All validation tests passing