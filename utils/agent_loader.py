"""
Shared agent loading utilities for all match runners.

Reads agent source files, extracts the agent class and its imports, renames
the class with an index suffix to avoid collisions when two agents are
embedded in the same subprocess script.
"""

import re
from pathlib import Path

from logging_config import setup_logging

logger = setup_logging("agent-loader")

AGENTS_DIR = Path(__file__).parent.parent / "agents"


def load_stored_agent(
    model_folder: str, game: str, run: int, agent_idx: int, class_name: str
) -> tuple[str, str]:
    """Load agent code from a stored file and extract ONLY the agent class.

    Reads the agent source, collects all import lines that appear before the
    class definition, then extracts the class body and renames it with an
    ``_{agent_idx}`` suffix.

    Args:
        model_folder: Directory name under agents/ (sanitized model name).
        game: Game file stem, e.g. ``"A1-Battleship"``.
        run: Run number (1-based).
        agent_idx: Numeric suffix appended to the class name (1 or 2).
        class_name: Expected class name, e.g. ``"BattleshipAgent"``.

    Returns:
        Tuple of (agent_class_code, import_lines) where import_lines is a
        newline-joined string of all ``import`` / ``from`` statements found
        before the class definition.
    """
    agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"

    if not agent_file.exists():
        logger.error("Agent file not found: %s", agent_file)
        return "", ""

    content = agent_file.read_text()
    code_lines = content.split("\n")

    # Collect imports before the class definition
    imports: list[str] = []
    class_start_idx: int | None = None

    for i, line in enumerate(code_lines):
        stripped = line.strip()

        if stripped.startswith(f"class {class_name}"):
            class_start_idx = i
            break

        if stripped.startswith("import ") or stripped.startswith("from "):
            imports.append(stripped)

    if class_start_idx is None:
        logger.error("No %s class found in %s", class_name, agent_file)
        return "", ""

    # Extract the class body (stop at next top-level definition)
    class_lines: list[str] = []
    base_indent = 0

    for i in range(class_start_idx, len(code_lines)):
        line = code_lines[i]
        stripped = line.strip()

        if i == class_start_idx:
            class_lines.append(line)
            base_indent = len(line) - len(line.lstrip())
            continue

        if not stripped or stripped.startswith("#"):
            class_lines.append(line)
            continue

        current_indent = len(line) - len(line.lstrip())
        if current_indent <= base_indent:
            break

        class_lines.append(line)

    agent_code = "\n".join(class_lines)
    agent_code = re.sub(
        rf"\b{class_name}\b", f"{class_name}_{agent_idx}", agent_code
    )

    return agent_code.strip(), "\n".join(imports)


COMMON_HEADER_IMPORTS: set[str] = {
    "import sys",
    "import random",
    "import signal",
    "import time",
    "import collections",
    "import math",
    "import itertools",
    "import copy",
}


def consolidate_imports(
    imp1: str, imp2: str, header_imports: set[str] | None = None
) -> str:
    """Merge two newline-separated import strings, removing duplicates.

    Lines that exactly match an entry in ``header_imports`` are excluded
    since they are already provided by the subprocess header.

    Args:
        imp1: Newline-separated imports from agent 1.
        imp2: Newline-separated imports from agent 2.
        header_imports: Import lines already present in the subprocess
            header.  Defaults to :data:`COMMON_HEADER_IMPORTS` when
            ``None``.
    """
    exclude = header_imports if header_imports is not None else COMMON_HEADER_IMPORTS
    all_imports = set(imp1.split("\n") + imp2.split("\n"))
    return "\n".join(
        imp for imp in sorted(all_imports) if imp.strip() and imp not in exclude
    )
