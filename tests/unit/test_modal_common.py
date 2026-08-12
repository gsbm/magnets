"""Unit tests for the shared modal-operator helpers (bpy-free)."""

# ops.modal_common imports only mathutils, so it is safe in the bpy-free suite.
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

from mathutils import Vector

_PKG = Path(__file__).resolve().parents[2] / "magnets"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

_spec = importlib.util.spec_from_file_location(
    "magnets_modal_common", _PKG / "ops" / "modal_common.py"
)
modal_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(modal_common)

AxisConstraint = modal_common.AxisConstraint


@dataclass
class FakeEvent:
    type: str
    value: str = "PRESS"


def test_axis_starts_free():
    ax = AxisConstraint()
    assert not ax.active
    assert ax.name == ""
    assert ax.axis_vector() is None
    d = Vector((1.0, 2.0, 3.0))
    assert ax.project(d) == d


def test_axis_lock_and_toggle_off():
    ax = AxisConstraint()
    assert ax.handle_key(FakeEvent("Y"))
    assert ax.active and ax.name == "Y"
    assert ax.axis_vector() == Vector((0.0, 1.0, 0.0))
    # Pressing the same axis again releases the lock.
    assert ax.handle_key(FakeEvent("Y"))
    assert not ax.active


def test_axis_switch_between_axes():
    ax = AxisConstraint()
    ax.handle_key(FakeEvent("X"))
    ax.handle_key(FakeEvent("Z"))
    assert ax.name == "Z"
    assert ax.project(Vector((5.0, 6.0, 7.0))) == Vector((0.0, 0.0, 7.0))


def test_axis_ignores_non_axis_and_release():
    ax = AxisConstraint()
    assert not ax.handle_key(FakeEvent("Q"))
    assert not ax.handle_key(FakeEvent("X", value="RELEASE"))
    assert not ax.active


def test_nav_passthrough_membership():
    assert modal_common.is_nav_event(FakeEvent("WHEELUPMOUSE"))
    assert not modal_common.is_nav_event(FakeEvent("MIDDLEMOUSE"))
    assert not modal_common.is_nav_event(FakeEvent("MOUSEMOVE"))
