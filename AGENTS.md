# Project Agents.md Guide for AI Agents

This `AGENTS.md` file provides comprehensive guidance for AI coding assistants (e.g., OpenAI Codex, ChatGPT) when working with the **zlog-discord** Python project.

---

## Project Structure

- `/src/zlog-discord`: Main Python package
  - `autogen.py`: Script to auto-generate SQLAlchemy models from the database schema
  - `models.py`: Generated SQLAlchemy Declarative models
  - `model_test.py`: Tests generated models against the live database
- `/tests`: Python test files (pytest recommended)
- `pyproject.toml`: Poetry configuration (dependencies, scripts, metadata)
- `docker-compose.yml`: Docker setup for local services
- `.env`: Environment variables for database and secrets

---

## Coding Conventions

### General Guidelines
- Use **Python 3.11+** (enforced via `pyenv` + Poetry)
- Follow **PEP 8** for code style
- Use **type hints** in new code
- Add **docstrings** for all functions and classes
- Favor **meaningful names** for variables and functions
- Keep modules small and focused

### SQLAlchemy Models
- Models are auto-generated via `autogen.py`
- Manual edits should **not** go into `models.py` (regenerate instead)
- If extending models, create a `custom_models.py` to avoid overwriting

### Environment Variables
- Managed with `.env`
- Always access using `os.getenv()` after `dotenv.load_dotenv()`
- Keep secrets out of version control

---

## Testing Guidelines

Use **pytest** for testing.

Commands:

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_example.py::test_function

# Run with coverage
poetry run pytest --cov=src/zlog-discord
```

Model verification can also be done with:

```bash
poetry run python src/zlog-discord/model_test.py
```

---

## Docker & Deployment

- Docker is used primarily for running services, not for Python execution
- Remote Docker host is accessible over Tailscale (`docker` machine)
- Ensure environment is configured for **remote Docker daemon** in PyCharm if needed

---

## Pull Request Guidelines

1. Include a clear description of the change
2. Reference related issues
3. Ensure all tests pass
4. Keep PRs focused on a single concern
5. Update documentation if functionality changes

---

## Programmatic Checks

Before merging changes, run:

```bash
# Lint
poetry run black src tests
poetry run flake8 src tests

# Type check
poetry run mypy src

# Tests
poetry run pytest
```

All checks must pass before merging AI-generated contributions.

---

## Notes for AI Agents

- Never hardcode database credentials — always use `.env`
- Prefer `sqlalchemy` ORM for queries; avoid raw SQL unless necessary
- Regenerate `models.py` with `autogen.py` if the schema changes
- Use `Session` from `sqlalchemy.orm.sessionmaker` for DB interactions
- Keep generated code **idempotent and safe to re-run**
