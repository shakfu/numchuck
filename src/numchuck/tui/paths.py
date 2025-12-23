"""
Path management for numchuck CLI

Provides centralized management of user directories and files for:
- REPL history
- Code snippets
- Sessions/projects
- Logs
- Configuration
"""

from pathlib import Path


def get_numchuck_home() -> Path:
    """
    Get the numchuck home directory (~/.numchuck).

    Returns:
        Path to ~/.numchuck directory
    """
    return Path.home() / ".numchuck"


def get_snippets_dir() -> Path:
    """
    Get the snippets directory (~/.numchuck/snippets).

    This directory stores reusable ChucK code snippets that can be
    loaded with the @<name> command in the REPL.

    Returns:
        Path to ~/.numchuck/snippets directory
    """
    return get_numchuck_home() / "snippets"


def get_history_file() -> Path:
    """
    Get the REPL history file path (~/.numchuck/history).

    Returns:
        Path to ~/.numchuck/history file
    """
    return get_numchuck_home() / "history"


def get_sessions_dir() -> Path:
    """
    Get the sessions directory (~/.numchuck/sessions).

    This directory can store saved REPL sessions, allowing users to
    save and restore their work.

    Returns:
        Path to ~/.numchuck/sessions directory
    """
    return get_numchuck_home() / "sessions"


def get_logs_dir() -> Path:
    """
    Get the logs directory (~/.numchuck/logs).

    This directory can store ChucK VM logs, audio engine logs,
    and REPL debugging output.

    Returns:
        Path to ~/.numchuck/logs directory
    """
    return get_numchuck_home() / "logs"


def get_config_file() -> Path:
    """
    Get the configuration file path (~/.numchuck/config.toml).

    This file can store user preferences like:
    - Default sample rate
    - Default audio device
    - REPL appearance settings
    - Default chugin paths

    Returns:
        Path to ~/.numchuck/config.toml file
    """
    return get_numchuck_home() / "config.toml"


def get_projects_dir() -> Path:
    """
    Get the projects directory (~/.numchuck/projects).

    This directory can store multi-file ChucK projects with:
    - Main .ck files
    - Dependencies
    - Audio samples
    - Project configuration

    Returns:
        Path to ~/.numchuck/projects directory
    """
    return get_numchuck_home() / "projects"


def ensure_numchuck_directories():
    """
    Ensure all numchuck directories exist.

    Creates ~/.numchuck and standard subdirectories if they don't exist:
    - snippets/
    - sessions/
    - logs/
    - projects/
    """
    # Create main directory
    numchuck_home = get_numchuck_home()
    numchuck_home.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    get_snippets_dir().mkdir(exist_ok=True)
    get_sessions_dir().mkdir(exist_ok=True)
    get_logs_dir().mkdir(exist_ok=True)
    get_projects_dir().mkdir(exist_ok=True)


def list_snippets() -> list[str]:
    """
    List all available snippets.

    Returns:
        List of snippet names (without .ck extension)
    """
    snippets_dir = get_snippets_dir()
    if not snippets_dir.exists():
        return []

    return [f.stem for f in snippets_dir.glob("*.ck")]


def get_snippet_path(name: str) -> Path:
    """
    Get the path to a snippet by name.

    Args:
        name: Snippet name (without .ck extension)

    Returns:
        Path to the snippet file
    """
    return get_snippets_dir() / f"{name}.ck"


def list_projects() -> list[str]:
    """
    List all available projects.

    Returns:
        List of project names (directory names in ~/.numchuck/projects/)
    """
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return []

    return [d.name for d in projects_dir.iterdir() if d.is_dir()]


def create_project(name: str) -> Path:
    """
    Create a new project directory.

    Args:
        name: Project name

    Returns:
        Path to the created project directory
    """
    from .project import Project

    projects_dir = get_projects_dir()
    project = Project(name, projects_dir)
    return project.project_dir


def get_project_path(name: str) -> Path:
    """
    Get the path to a project by name.

    Args:
        name: Project name

    Returns:
        Path to the project directory
    """
    return get_projects_dir() / name
