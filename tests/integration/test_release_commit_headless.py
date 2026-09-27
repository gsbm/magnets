"""Headless coverage for the snap-on-release path.

Runs ``release_commit_inner.py`` in ``blender --background``: session start,
drag ticks (guides and landing preview), the translate/rotate/scale commit
with its guards, and the timer state machine, using a synthetic viewport.
Skipped when no Blender binary is found (``BLENDER_BIN`` or ``blender`` on
PATH).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INNER = Path(__file__).with_name("release_commit_inner.py")


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_release_commit_headless():
    blender = _blender_bin()
    if not blender:
        pytest.skip("no Blender binary (set BLENDER_BIN or add blender to PATH)")

    proc = subprocess.run(
        [blender, "--background", "--factory-startup", "--python", str(INNER),
         "--", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    assert "MAGNETS_RELEASE_OK" in proc.stdout, "release/commit checks failed"
