# Claude Instructions

## Commit Message Guidelines

- No marketing language in commit messages
- Keep commit messages concise and descriptive
- Focus on what was changed, not promotional language
- Example: "Fix code formatting and CI/CD compliance across all MLOps services" (good)
- Avoid: Marketing terms, emojis, or promotional language (bad)

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

## Testing Requirements

- All tests must pass before committing
- 47 unit/integration tests currently passing
- E2E tests available but may be skipped in CI