"""Opt-in live tests of the snap-on-release path (needs a display).

Runs a *windowed* Blender per scenario with simulated mouse events; see
``release_scenarios.py``. Skipped unless ``MAGNETS_LIVE=1``::

    MAGNETS_LIVE=1 BLENDER_BIN=/path/to/blender pytest tests/live -m live

Each run uses a throwaway ``BLENDER_USER_RESOURCES`` so the user's own Blender
configuration and extensions are never touched.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ["translate", "yield", "xlock", "rotate", "scale", "edit_small", "edit_large"]

pytestmark = pytest.mark.live


def _blender_bin() -> str | None:
    return os.environ.get("BLENDER_BIN") or shutil.which("blender")


@pytest.fixture(scope="module")
def built_zip(tmp_path_factory):
    out = subprocess.run(
        [sys.executable, str(REPO_ROOT / "build" / "build_zip.py")],
        capture_output=True, text=True, check=True,
    )
    zips = sorted((REPO_ROOT / "dist").glob("magnets-*.zip"))
    assert zips, out.stdout + out.stderr
    return zips[-1]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_release_scenario(scenario, built_zip, tmp_path):
    if os.environ.get("MAGNETS_LIVE") != "1":
        pytest.skip("set MAGNETS_LIVE=1 to run windowed Blender live tests")
    blender = _blender_bin()
    if not blender:
        pytest.skip("no Blender binary (set BLENDER_BIN or add blender to PATH)")

    # A saved .blend skips the splash screen that would cover the viewport.
    scene = tmp_path / "scene.blend"
    subprocess.run(
        [blender, "--background", "--factory-startup", "--python-expr",
         f"import bpy; bpy.ops.wm.save_as_mainfile(filepath={str(scene)!r})"],
        capture_output=True, text=True, check=True, timeout=120,
    )
    env = dict(os.environ, BLENDER_USER_RESOURCES=str(tmp_path / "user"))
    proc = subprocess.run(
        [blender, "--factory-startup", "--enable-event-simulate", str(scene),
         "--python", str(REPO_ROOT / "tests" / "live" / "release_scenarios.py"),
         "--", str(built_zip), scenario],
        capture_output=True, text=True, check=False, timeout=120, env=env,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("LIVE_RESULT")]
    sys.stdout.write("\n".join(lines) + "\n")
    assert lines, proc.stdout[-2000:] + proc.stderr[-2000:]
    failures = [ln for ln in lines if " FAIL " in ln]
    assert not failures, "\n".join(failures)
