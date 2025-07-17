"""Utilities for code synthesis based on repository context."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from . import configure_logging

logger = logging.getLogger(__name__)


class CodeSynthesizer:
    """Generate code for function specifications."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root)

    def _collect_files(self, base: Path, limit: int) -> List[Path]:
        return list(base.rglob("*.py"))[:limit]

    def synthesize(self, function_spec: dict) -> List[Path]:
        """Return repository files relevant to ``function_spec``."""
        configure_logging()
        file_limit = int(os.getenv("CODE_SYNTH_FILE_LIMIT", "20"))
        src_dir = self.repo_root / "src" / "auto"
        mig_dir = self.repo_root / "alembic" / "versions"
        context_path = self.repo_root / "CONTEXT.md"
        context = context_path.read_text(encoding="utf-8")
        logger.debug("Loaded context: %s...", context[:100])
        files = self._collect_files(src_dir, file_limit)
        files += self._collect_files(mig_dir, file_limit)
        logger.info("Prepared repository context with %d files", len(files))
        # Placeholder for real synthesis
        return files
