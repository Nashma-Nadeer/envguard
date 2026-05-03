"""
envguard/scanner.py — Core scanning logic for .env files
"""

import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

# ── Patterns that look like real secrets ────────────────────────────────────
SECRET_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd)=\S+'), "Possible plaintext password"),
    (re.compile(r'(?i)(secret|token|api_key|apikey|access_key)=\S{4,}'), "Possible secret / token"),
    (re.compile(r'(?i)(aws_secret|aws_access)=\S+'), "AWS credential detected"),
    (re.compile(r'(?i)private_key=\S+'), "Private key value detected"),
    (re.compile(r'(?i)(database_url|db_url)=(postgres|mysql|mongodb)\S+'), "Database URL with credentials"),
    (re.compile(r'(sk-|ghp_|gho_|glpat-)[A-Za-z0-9_\-]{6,}'), "Known secret prefix detected"),
]

# ── Patterns for weak / placeholder values ───────────────────────────────────
WEAK_PATTERNS = [
    (re.compile(r'(?i)=\s*(password|changeme|secret|test|1234|admin|root|example)$'), "Weak/placeholder value"),
    (re.compile(r'(?i)=\s*your[_-]?\w+$'), "Unfilled placeholder value"),
    (re.compile(r'(?i)=\s*<\w+>$'), "Template placeholder not replaced"),
    (re.compile(r'(?i)=\s*xxx+$'), "XXX placeholder value"),
]


@dataclass
class Issue:
    level: str          # "error" | "warning" | "info"
    line_no: int
    key: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ScanResult:
    file_path: str
    issues: List[Issue] = field(default_factory=list)
    total_vars: int = 0
    missing_from_schema: List[str] = field(default_factory=list)
    gitignore_safe: Optional[bool] = None

    @property
    def errors(self):
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.level == "warning"]

    @property
    def passed(self):
        return len(self.errors) == 0


def parse_env_file(path: Path) -> List[tuple]:
    """Return list of (line_no, key, raw_line) from a .env file."""
    entries = []
    lines = []

    # Try different encodings to handle Windows UTF-16 files
    for encoding in ["utf-8-sig", "utf-16", "utf-8", "latin-1"]:
        try:
            with open(path, "r", encoding=encoding) as f:
                lines = f.readlines()
            # Verify it looks like an env file
            if any("=" in line for line in lines):
                break
        except Exception:
            continue

    for i, line in enumerate(lines, 1):
        stripped = line.strip().strip('\x00')
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            entries.append((i, key, stripped))
    return entries


def check_gitignore(env_path: Path) -> Optional[bool]:
    """Return True if .env is listed in .gitignore, False if not, None if no .gitignore found."""
    gitignore = env_path.parent / ".gitignore"
    if not gitignore.exists():
        return None
    content = gitignore.read_text(encoding="utf-8", errors="replace")
    patterns = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    filename = env_path.name
    for pat in patterns:
        if pat in (filename, f"/{filename}", "*.env", ".env*"):
            return True
    return False


def scan_file(env_path: Path, schema_path: Optional[Path] = None) -> ScanResult:
    result = ScanResult(file_path=str(env_path))

    if not env_path.exists():
        result.issues.append(Issue("error", 0, "", f"File not found: {env_path}"))
        return result

    entries = parse_env_file(env_path)
    result.total_vars = len(entries)
    defined_keys = {key for _, key, _ in entries}

    for line_no, key, raw in entries:
        # Check secret patterns
        for pattern, message in SECRET_PATTERNS:
            if pattern.search(raw):
                result.issues.append(Issue(
                    level="error",
                    line_no=line_no,
                    key=key,
                    message=message,
                    suggestion="Move this value to a secrets manager (e.g. AWS Secrets Manager, Vault) and reference it at runtime."
                ))
                break

        # Check weak values
        for pattern, message in WEAK_PATTERNS:
            if pattern.search(raw):
                result.issues.append(Issue(
                    level="warning",
                    line_no=line_no,
                    key=key,
                    message=message,
                    suggestion="Replace with a strong, unique value before deploying."
                ))
                break

        # Check for empty value
        if re.match(r'^[A-Z_]+=\s*$', raw, re.IGNORECASE):
            result.issues.append(Issue(
                level="warning",
                line_no=line_no,
                key=key,
                message="Empty value — intentional?",
                suggestion="If optional, add a comment. If required, provide a value."
            ))

    # Schema validation
    if schema_path and schema_path.exists():
        schema_keys = []
        with open(schema_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    schema_keys.append(line.split("=")[0].strip())
        result.missing_from_schema = [k for k in schema_keys if k not in defined_keys]

    # Gitignore check
    result.gitignore_safe = check_gitignore(env_path)

    return result