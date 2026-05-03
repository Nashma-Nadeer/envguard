"""
envguard/cli.py — Command-line interface
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import track

from envguard.scanner import scan_file, ScanResult

app = typer.Typer(
    name="envguard",
    help="🛡️  Scan .env files for exposed secrets, weak values, and missing variables.",
    add_completion=False,
)
console = Console()


def _level_style(level: str) -> str:
    return {"error": "bold red", "warning": "bold yellow", "info": "dim"}.get(level, "white")


def _level_icon(level: str) -> str:
    return {"error": "✖️", "warning": "⚠️", "info": "ℹ️"}.get(level, "·")


def _print_result(result: ScanResult, verbose: bool = False):
    path_label = f"[bold cyan]{result.file_path}[/bold cyan]"

    if not result.issues and not result.missing_from_schema:
        console.print(f"  {path_label}  [bold green]✔️ All clear[/bold green] ({result.total_vars} vars)")
        return

    console.print(f"\n  {path_label}  [dim]{result.total_vars} vars[/dim]")

    # Issues table
    if result.issues:
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
        table.add_column("", width=2)
        table.add_column("Line", style="dim", width=6)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Issue")
        if verbose:
            table.add_column("Suggestion", style="dim italic")

        for issue in result.issues:
            row = [
                Text(_level_icon(issue.level), style=_level_style(issue.level)),
                str(issue.line_no) if issue.line_no else "—",
                issue.key or "—",
                Text(issue.message, style=_level_style(issue.level)),
            ]
            if verbose:
                row.append(issue.suggestion or "")
            table.add_row(*row)

        console.print(table)

    # Missing schema keys
    if result.missing_from_schema:
        console.print(f"  [bold yellow]⚠️  Missing required vars:[/bold yellow] {', '.join(result.missing_from_schema)}")

    # Gitignore status
    if result.gitignore_safe is False:
        console.print("  [bold red]✖️  .env is NOT in .gitignore — risk of accidental commit![/bold red]")
    elif result.gitignore_safe is None:
        console.print("  [yellow]⚠️  No .gitignore found in this directory.[/yellow]")


@app.command()
def scan(
    paths: list[Path] = typer.Argument(
        default=None,
        help="One or more .env files to scan. Defaults to .env in current directory.",
    ),
    schema: Optional[Path] = typer.Option(
        None, "--schema", "-s",
        help="Path to a .env.example or schema file listing required keys.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show fix suggestions alongside each issue.",
    ),
    strict: bool = typer.Option(
        False, "--strict",
        help="Exit with code 1 even on warnings (not just errors).",
    ),
):
    """
    Scan one or more .env files for security issues.

    Examples:\n
      envguard                          # scan .env in current dir\n
      envguard .env.production          # scan a specific file\n
      envguard .env -s .env.example     # validate against a schema\n
      envguard .env --verbose           # show fix suggestions\n
    """
    if not paths:
        paths = [Path(".env")]

    console.print(Panel.fit(
        "[bold white]envguard[/bold white] [dim]— .env security scanner[/dim]",
        border_style="cyan",
    ))

    all_results: list[ScanResult] = []

    for p in track(paths, description="Scanning...", transient=True):
        result = scan_file(p, schema_path=schema)
        all_results.append(result)
        _print_result(result, verbose=verbose)

    # Summary
    total_errors = sum(len(r.errors) for r in all_results)
    total_warnings = sum(len(r.warnings) for r in all_results)
    total_missing = sum(len(r.missing_from_schema) for r in all_results)

    console.print()
    if total_errors == 0 and total_warnings == 0 and total_missing == 0:
        console.print(Panel(
            "[bold green]✔️  No issues found. Your .env looks safe![/bold green]",
            border_style="green",
        ))
    else:
        parts = []
        if total_errors:
            parts.append(f"[red]{total_errors} error{'s' if total_errors > 1 else ''}[/red]")
        if total_warnings:
            parts.append(f"[yellow]{total_warnings} warning{'s' if total_warnings > 1 else ''}[/yellow]")
        if total_missing:
            parts.append(f"[yellow]{total_missing} missing var{'s' if total_missing > 1 else ''}[/yellow]")
        console.print(Panel(
            "  ".join(parts) + "\n[dim]Run with --verbose for fix suggestions.[/dim]",
            title="[bold]Scan Summary[/bold]",
            border_style="red" if total_errors else "yellow",
        ))

    if total_errors > 0 or (strict and total_warnings > 0):
        raise typer.Exit(code=1)


@app.command()
def init(
    output: Path = typer.Argument(Path(".env.example"), help="Output path for the schema file."),
    source: Path = typer.Option(Path(".env"), "--from", help="Existing .env to generate schema from."),
):
    """
    Generate a .env.example schema from an existing .env file (values are stripped).
    """
    if not source.exists():
        console.print(f"[red]✖️  Source file not found:[/red] {source}")
        raise typer.Exit(1)

    lines_out = []
    with open(source) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                lines_out.append(line)
            elif "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                lines_out.append(f"{key}=\n")
            else:
                lines_out.append(line)

    with open(output, "w") as f:
        f.writelines(lines_out)

    console.print(f"[green]✔️  Schema written to[/green] [cyan]{output}[/cyan]")


def main():
    app()


if __name__ == "__main__":
    main()