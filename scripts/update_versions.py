"""Inspect project changes, update release versions, and create a Git commit."""

from __future__ import annotations

import re
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

import questionary
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm
from rich.table import Table

from cli_utils import run_cli_with_keyboard_interrupt
from utils.version_file_updates import build_file_updates
from utils.version_update_models import (
    PROJECT_CONFIGS,
    BumpLevel,
    GitCommit,
    ProjectConfig,
    ProjectUpgradePlan,
    SemanticVersion,
    VersionUpdateError,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MAX_COMMIT_SUMMARIES = 3


def run_git(
    repo_root: Path, arguments: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run Git without a shell and capture its text output.

    Args:
        repo_root: Repository working directory.
        arguments: Arguments following the ``git`` executable.
        check: Whether a nonzero exit code should raise an error.

    Returns:
        Completed Git process.

    Raises:
        VersionUpdateError: If Git cannot run or exits unsuccessfully when checked.
    """
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise VersionUpdateError(f"无法执行 Git: {exc}") from exc
    if check and completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        raise VersionUpdateError(
            f"Git 命令执行失败: git {' '.join(arguments)}\n{details}"
        )
    return completed


def assert_clean_worktree(repo_root: Path) -> None:
    """Require a completely clean tracked and untracked Git worktree.

    Args:
        repo_root: Repository to inspect.

    Raises:
        VersionUpdateError: If the directory is not a repository or contains changes.
    """
    run_git(repo_root, ["rev-parse", "--show-toplevel"])
    status = run_git(
        repo_root, ["status", "--porcelain=v1", "--untracked-files=all"]
    ).stdout.rstrip()
    if status:
        raise VersionUpdateError(f"工作区存在未提交项，请先提交或清理：\n{status}")


def read_canonical_version(repo_root: Path, config: ProjectConfig) -> SemanticVersion:
    """Read the canonical version for one project.

    Args:
        repo_root: Repository containing the project.
        config: Project version-source configuration.

    Returns:
        Parsed canonical semantic version.

    Raises:
        VersionUpdateError: If the source is missing, malformed, or ambiguous.
    """
    path = repo_root / config.canonical_path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VersionUpdateError(f"无法读取版本文件 {path}: {exc}") from exc

    if config.canonical_kind == "typescript":
        matches = re.findall(r"(?m)^\s*version:\s*'([^']+)'\s*$", text)
        if len(matches) != 1:
            raise VersionUpdateError(
                f"{config.canonical_path} 必须包含唯一的 version 字段"
            )
        value = matches[0]
    else:
        try:
            document = tomllib.loads(text)
            value = document["project"]["version"]
        except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
            raise VersionUpdateError(
                f"无法解析 {config.canonical_path} 的 project.version"
            ) from exc
        if not isinstance(value, str):
            raise VersionUpdateError(
                f"{config.canonical_path} 的 project.version 必须是字符串"
            )
    return SemanticVersion.parse(value, source=str(config.canonical_path))


def find_baseline_commit(repo_root: Path, config: ProjectConfig) -> str:
    """Find the latest version commit for one project.

    Args:
        repo_root: Repository whose history is inspected.
        config: Project Git and canonical-source configuration.

    Returns:
        Full commit hash used as the exclusive change baseline.

    Raises:
        VersionUpdateError: If no project history can be found.
    """
    version_history = run_git(
        repo_root,
        [
            "log",
            "--format=%H%x09%s",
            "--",
            str(config.project_path),
        ],
    ).stdout.splitlines()
    for entry in version_history:
        commit_hash, separator, subject = entry.partition("\t")
        if separator and subject.startswith("Version:"):
            return commit_hash

    field_commit = run_git(
        repo_root,
        [
            "log",
            "-n",
            "1",
            f"-G{config.version_history_pattern}",
            "--format=%H",
            "--",
            str(config.canonical_path),
        ],
    ).stdout.strip()
    if field_commit:
        return field_commit

    history = run_git(
        repo_root,
        ["log", "--reverse", "--format=%H", "--", str(config.project_path)],
    ).stdout.splitlines()
    if not history:
        raise VersionUpdateError(f"找不到 {config.display_name} 的 Git 历史")
    return history[0]


def collect_commits(
    repo_root: Path, config: ProjectConfig, baseline: str
) -> list[GitCommit]:
    """Collect project commits after an exclusive baseline.

    Args:
        repo_root: Repository whose history is inspected.
        config: Project path configuration.
        baseline: Exclusive starting commit hash.

    Returns:
        Newest-first relevant commits.

    Raises:
        VersionUpdateError: If Git cannot traverse the requested range.
    """
    output = run_git(
        repo_root,
        [
            "log",
            "--format=%H%x09%s",
            f"{baseline}..HEAD",
            "--",
            str(config.project_path),
        ],
    ).stdout
    commits: list[GitCommit] = []
    for line in output.splitlines():
        commit_hash, separator, subject = line.partition("\t")
        if not separator:
            raise VersionUpdateError(f"无法解析 {config.display_name} 的 Git 提交记录")
        commits.append(GitCommit(commit_hash, subject))
    return commits


def create_upgrade_plans(repo_root: Path) -> list[ProjectUpgradePlan]:
    """Build change and version plans for every configured project.

    Args:
        repo_root: Repository to inspect.

    Returns:
        Plans ordered as Web, API, and Core.

    Raises:
        VersionUpdateError: If versions or Git history cannot be read.
    """
    plans: list[ProjectUpgradePlan] = []
    for config in PROJECT_CONFIGS:
        baseline = find_baseline_commit(repo_root, config)
        plans.append(
            ProjectUpgradePlan(
                config=config,
                current_version=read_canonical_version(repo_root, config),
                baseline_commit=baseline,
                commits=collect_commits(repo_root, config, baseline),
            )
        )
    return plans


def prompt_for_bump_level(plan: ProjectUpgradePlan, console: Console) -> BumpLevel:
    """Prompt for one changed project's independent increment level.

    Args:
        plan: Changed project awaiting a decision.
        console: Rich console used for output and input.

    Returns:
        Selected increment level or ``SKIP``.
    """
    console.print()
    console.rule(f"[bold cyan]{plan.config.display_name}[/bold cyan]")
    console.print(f"当前版本: [bold]{plan.current_version}[/bold]")
    for commit in plan.commits[:MAX_COMMIT_SUMMARIES]:
        console.print(
            f"  [cyan]{commit.commit_hash[:8]}[/cyan] {escape(commit.subject)}"
        )
    omitted_count = len(plan.commits) - MAX_COMMIT_SUMMARIES
    if omitted_count > 0:
        console.print(f"  [dim]另有 {omitted_count} 条提交未显示[/dim]")
    try:
        selected_level = questionary.select(
            "选择递增级别",
            choices=[
                questionary.Choice(title=level.value, value=level)
                for level in BumpLevel
            ],
            default=BumpLevel.PATCH,
            use_arrow_keys=True,
            use_jk_keys=False,
            use_search_filter=True,
            instruction="(方向键切换，输入筛选，Enter 确认)",
        ).unsafe_ask()
    except EOFError as exc:
        raise VersionUpdateError("递增级别选择需要交互式终端") from exc
    if not isinstance(selected_level, BumpLevel):
        raise VersionUpdateError("未选择有效的递增级别")
    return selected_level


def choose_project_levels(
    plans: list[ProjectUpgradePlan],
    *,
    console: Console,
    choose_level: Callable[[ProjectUpgradePlan], BumpLevel] | None = None,
) -> None:
    """Choose and calculate an independent target for every changed project.

    Args:
        plans: Mutable project plans to populate.
        console: Rich console used by the default prompt.
        choose_level: Optional injected chooser used by tests or automation.
    """
    chooser = choose_level or (lambda plan: prompt_for_bump_level(plan, console))
    for plan in plans:
        if not plan.has_changes:
            continue
        plan.bump_level = chooser(plan)
        if plan.bump_level is not BumpLevel.SKIP:
            plan.target_version = plan.current_version.bump(plan.bump_level)


def render_upgrade_table(plans: list[ProjectUpgradePlan], console: Console) -> None:
    """Render the final project upgrade list with status colors.

    Args:
        plans: Plans whose choices and targets are displayed.
        console: Rich console receiving the table.
    """
    table = Table(title="项目版本升级列表", show_lines=False)
    table.add_column("项目")
    table.add_column("状态")
    table.add_column("提交数", justify="right")
    table.add_column("当前版本")
    table.add_column("递增级别")
    table.add_column("目标版本")
    for plan in plans:
        if plan.should_upgrade:
            style = "green"
            status = "待升级"
        elif plan.has_changes:
            style = "yellow"
            status = "已跳过"
        else:
            style = "dim"
            status = "无变更"
        table.add_row(
            plan.config.display_name,
            status,
            str(len(plan.commits)),
            str(plan.current_version),
            plan.bump_level.value if plan.bump_level else "-",
            str(plan.target_version) if plan.target_version else "-",
            style=style,
        )
    console.print()
    console.print(table)


def commit_version_updates(
    repo_root: Path,
    plans: list[ProjectUpgradePlan],
    updates: dict[Path, bytes],
) -> str:
    """Write, stage, and commit selected version updates with rollback on failure.

    Args:
        repo_root: Clean repository to update.
        plans: Selected plans used to compose the commit subject.
        updates: Fully validated target file bytes.

    Returns:
        Short hash of the created commit.

    Raises:
        VersionUpdateError: If writing, staging, or committing fails.
    """
    originals = {path: path.read_bytes() for path in updates}
    relative_paths = [str(path.relative_to(repo_root)) for path in sorted(updates)]
    selected = [plan for plan in plans if plan.target_version is not None]
    subject = "Version: " + ", ".join(
        f"{plan.config.display_name} {plan.target_version}" for plan in selected
    )
    try:
        for path, content in updates.items():
            path.write_bytes(content)
        run_git(repo_root, ["add", "--", *relative_paths])
        run_git(repo_root, ["commit", "-m", subject])
    except (OSError, VersionUpdateError) as exc:
        for path, content in originals.items():
            path.write_bytes(content)
        run_git(repo_root, ["add", "--", *relative_paths], check=False)
        if isinstance(exc, VersionUpdateError):
            raise
        raise VersionUpdateError(f"写入版本文件失败: {exc}") from exc
    return run_git(repo_root, ["rev-parse", "--short", "HEAD"]).stdout.strip()


def main(
    *,
    repo_root: Path = REPO_ROOT,
    console: Console | None = None,
    choose_level: Callable[[ProjectUpgradePlan], BumpLevel] | None = None,
    confirm_upgrade: Callable[[], bool] | None = None,
) -> int:
    """Run the interactive version inspection, selection, update, and commit flow.

    Args:
        repo_root: Repository to update.
        console: Optional Rich console for output and prompts.
        choose_level: Optional per-project level chooser for tests or automation.
        confirm_upgrade: Optional final confirmation callback.

    Returns:
        Zero for success, no changes, or user cancellation.

    Raises:
        VersionUpdateError: If repository validation, updates, or commit fail.
    """
    output_console = console or Console(highlight=False)
    assert_clean_worktree(repo_root)
    plans = create_upgrade_plans(repo_root)
    if any(plan.has_changes for plan in plans):
        choose_project_levels(plans, console=output_console, choose_level=choose_level)
    render_upgrade_table(plans, output_console)

    selected = [plan for plan in plans if plan.should_upgrade]
    if not selected:
        output_console.print("[yellow]没有需要提交的版本升级。[/yellow]")
        return 0

    confirmer = confirm_upgrade or (
        lambda: Confirm.ask(
            "确认执行以上版本升级并创建提交？", default=True, console=output_console
        )
    )
    if not confirmer():
        output_console.print("[yellow]已取消版本升级。[/yellow]")
        return 0

    # A second check prevents concurrent edits from being absorbed into the version commit.
    assert_clean_worktree(repo_root)
    updates = build_file_updates(repo_root, selected)
    commit_hash = commit_version_updates(repo_root, selected, updates)
    output_console.print(f"[green]版本升级完成，已创建提交 {commit_hash}。[/green]")
    return 0


def run_entrypoint(*, console: Console | None = None) -> int:
    """Run the CLI with friendly validation and keyboard-interrupt handling.

    Args:
        console: Optional Rich console used for messages.

    Returns:
        Process-compatible exit code.
    """
    output_console = console or Console(highlight=False)

    def run() -> int:
        """Convert expected version-update failures into a concise CLI result."""
        try:
            return main(console=output_console)
        except VersionUpdateError as exc:
            output_console.print(f"[red]ERROR: {escape(str(exc))}[/red]")
            return 1

    return run_cli_with_keyboard_interrupt(
        run,
        interrupt_message="已取消版本升级",
        console=output_console,
    )


if __name__ == "__main__":
    raise SystemExit(run_entrypoint())
