# 🤝 Contributing to SpotifyExporter

Thanks for your interest in contributing! Here's how to get started.

## 📋 Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## 🚀 Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/SpotifyExporter.git
cd SpotifyExporter
```

### 2. Install Dependencies
```bash
# Using uv (faster)
uv sync

# Or with pip
pip install -r requirements.txt
pip install pytest pytest-cov black ruff mypy
```

### 3. Install Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

## 🧪 Testing

Run tests locally:
```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ -v --cov=. --cov-report=html
```

## 📝 Code Style

We use:
- **Black** for formatting
- **Ruff** for linting
- **MyPy** for type checking

Run all checks:
```bash
black .
ruff check --fix
mypy .
```

Or let pre-commit do it automatically on commit.

## 🐛 Reporting Bugs

1. Check [existing issues](https://github.com/amitxd75/SpotifyExporter/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS

## ✨ Feature Requests

1. Open an issue describing the feature
2. Explain the use case and benefits
3. Wait for feedback before implementing

## 📦 Submitting Changes

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Write/update tests: `tests/test_*.py`
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Create a Pull Request with:
   - Clear description of changes
   - Reference to related issues
   - Test results

## 📚 Project Structure

```
SpotifyExporter/
├── main.py                 # Main entry point
├── models.py              # Pydantic data models
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── requirements.txt       # Dependencies
├── pyproject.toml         # Project config
├── tests/
│   └── test_spotify_exporter.py
├── .github/
│   └── workflows/
│       └── tests.yml      # CI/CD pipeline
└── README.md
```

## 🎯 Areas for Contribution

- [ ] Add more output formats (Parquet, SQLite)
- [ ] Implement date range filtering
- [ ] Add genre analysis features
- [ ] Improve error handling
- [ ] Expand test coverage
- [ ] Documentation improvements

## ✅ Checklist Before PR

- [ ] Tests pass locally (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] Linting clean (`ruff check .`)
- [ ] Type hints added (`mypy .`)
- [ ] Updated README if needed
- [ ] Tests added for new features

## 📞 Questions?

Open an issue or check existing discussions!

---

**Thanks for contributing! 🎵**