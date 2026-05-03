"""
tests/test_scanner.py
"""
import pytest
from pathlib import Path
import tempfile
import os

from envguard.scanner import scan_file, check_gitignore


def make_env(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def test_clean_env_has_no_issues():
    p = make_env("APP_NAME=myapp\nDEBUG=false\nPORT=8080\n")
    result = scan_file(p)
    assert result.passed
    assert len(result.issues) == 0
    assert result.total_vars == 3
    os.unlink(p)


def test_detects_plaintext_password():
    p = make_env("DB_PASSWORD=supersecret123\n")
    result = scan_file(p)
    assert not result.passed
    assert any("password" in i.message.lower() for i in result.errors)
    os.unlink(p)


def test_detects_aws_credentials():
    p = make_env("AWS_SECRET=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n")
    result = scan_file(p)
    assert not result.passed
    os.unlink(p)


def test_detects_weak_value():
    p = make_env("SECRET_KEY=changeme\n")
    result = scan_file(p)
    assert len(result.warnings) > 0
    os.unlink(p)


def test_detects_empty_value():
    p = make_env("DATABASE_URL=\n")
    result = scan_file(p)
    assert len(result.warnings) > 0
    os.unlink(p)


def test_schema_missing_keys():
    env = make_env("APP_NAME=myapp\n")
    schema = make_env("APP_NAME=\nSECRET_KEY=\nDATABASE_URL=\n")
    result = scan_file(env, schema_path=schema)
    assert "SECRET_KEY" in result.missing_from_schema
    assert "DATABASE_URL" in result.missing_from_schema
    os.unlink(env)
    os.unlink(schema)


def test_nonexistent_file():
    result = scan_file(Path("/nonexistent/.env"))
    assert not result.passed
    assert any("not found" in i.message.lower() for i in result.issues)


def test_comments_and_blank_lines_ignored():
    p = make_env("# This is a comment\n\nAPP_ENV=production\n")
    result = scan_file(p)
    assert result.total_vars == 1
    os.unlink(p)