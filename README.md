# 🛡️ envguard

**Scan `.env` files for exposed secrets, weak values, and missing variables — before they become incidents.**

[![CI](https://github.com/Nashma-Nadeer/envguard/actions/workflows/ci.yml/badge.svg)](https://github.com/Nashma-Nadeer/envguard/actions)
[![PyPI version](https://badge.fury.io/py/envguard.svg)](https://badge.fury.io/py/envguard)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

Leaked `.env` files are one of the most common causes of security incidents. `envguard` is a fast, zero-dependency CLI that catches problems **before** you push, deploy, or share your environment config.

---

## ✨ Features

- 🔍 **Secret detection** — catches passwords, API keys, tokens, AWS credentials, private keys, and more
- 💀 **Weak value detection** — flags placeholders like `changeme`, `secret`, `your_key_here`
- 📋 **Schema validation** — compare against `.env.example` to find missing required variables
- 🙈 **Gitignore check** — warns if your `.env` isn't protected from accidental commits
- 🏗️ **Schema generator** — auto-generate a `.env.example` from your existing `.env`
- 🎨 **Beautiful output** — rich terminal UI with color-coded severity levels
- ⚡ **Fast** — scans hundreds of variables instantly
- 🔧 **CI-ready** — exits with code `1` on errors, integrates with any pipeline

---

## 📦 Installation

pip install envguard

Or with pipx (recommended for CLI tools):

pipx install envguard

---

## 🚀 Usage

### Basic scan

envguard

envguard .env.production

envguard .env .env.staging .env.production

### Validate against a schema

envguard .env --schema .env.example

### Verbose mode

envguard .env --verbose

### Strict mode

envguard .env --strict

### Generate a schema from existing .env

envguard init

---

## 🔍 What gets detected

| Category | Examples |
|----------|----------|
| Plaintext secrets | DB_PASSWORD=hunter2, SECRET_KEY=abc123 |
| API tokens & keys | API_KEY=sk-..., GITHUB_TOKEN=ghp_... |
| AWS credentials | AWS_SECRET=..., AWS_ACCESS_KEY=... |
| Database URLs | DATABASE_URL=postgres://user:pass@host/db |
| Weak placeholders | SECRET=changeme, TOKEN=your_token_here |
| Unfilled templates | KEY=<your-key>, VALUE=xxx |
| Empty required vars | DATABASE_URL= |
| Gitignore exposure | .env not listed in .gitignore |
| Missing schema keys | Keys in .env.example absent from .env |

---

## 🔧 CI Integration

### GitHub Actions

- name: Scan .env files
  run: |
    pip install envguard
    envguard .env --schema .env.example --strict

---

## 🛠️ Development

git clone https://github.com/Nashma-Nadeer/envguard
cd envguard
pip install -e ".[dev]"
pytest tests/ -v

---

## 🗺️ Roadmap

- [ ] AWS Secrets Manager integration
- [ ] .env diff tool
- [ ] VSCode extension
- [ ] JSON / SARIF output for security toolchains
- [ ] Support for encrypted .env files (via SOPS)

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (git checkout -b feature/my-feature)
3. Commit your changes (git commit -m 'feat: add my feature')
4. Push to the branch (git push origin feature/my-feature)
5. Open a Pull Request

---

## 📄 License

MIT — see LICENSE for details.

---

Built with ❤️ to keep secrets secret.