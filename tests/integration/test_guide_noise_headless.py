"""Headless noise budget for the guide overlay.

Runs ``guide_noise_inner.py`` in ``blender --background``: scripted drags
through busy scenes in top, front, right and perspective views, checking
what the overlay draws each frame and that it clears on release.
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
INNER = Path(__file__).with_name("guide_noise_inner.py")


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.mark.integration
def test_guide_noise_headless():
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
    assert "MAGNETS_NOISE_OK" in proc.stdout, "guide noise checks failed"
