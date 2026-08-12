"""GPU draw handlers for the 3D View."""

from __future__ import annotations

from dataclasses import dataclass, field

import blf
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .glyphs import (
    circle_2d_line_pairs,
    dash_segments,
    extend_segment,
    square_2d_verts,
)

# ── Active-pulse constants ─────────────────────────────────────────────────────
PULSE_FRAMES = 3          # frames the brightness boost lasts
PULSE_ALPHA_BOOST = 0.30  # additive alpha during the pulse window

# ── Internal state ─────────────────────────────────────────────────────────────

@dataclass
class GuideDrawItem:
    """One guide segment + its per-item render colour (includes fade alpha)."""
    a: Vector
    b: Vector
    color: tuple[float, float, float, float]  # linear RGBA, already faded


@dataclass
class _State:
    """Mutable GPU draw-handler state."""
    guide_items: list[GuideDrawItem] = field(default_factory=list)
    tick_items: list[GuideDrawItem] = field(default_factory=list)

    # Screen-space markers (world positions → projected in _draw_px)
    snap_dots: list[Vector] = field(default_factory=list)        # circles
    intersection_dots: list[Vector] = field(default_factory=list)  # squares
    ghost_points: list[Vector] = field(default_factory=list)  # landing preview
    labels: list[tuple[Vector, str, str]] = field(default_factory=list)

    # Preferences snapshot (set each frame via set_state)
    active_color: tuple = (1.0, 0.012, 0.141, 1.0)
    passive_color: tuple = (1.0, 0.031, 0.219, 0.70)
    line_width: float = 1.0
    solid_lines: bool = True
    show_snap_dot: bool = True
    snap_dot_radius_px: int = 4
    show_intersection_dot: bool = True
    pulse_enabled: bool = True

    # Pulse state
    snapped_prev: bool = False
    pulse_frame: int = 0

    active: bool = False


_state = _State()

_handle_view: object | None = None
_handle_px: object | None = None
_shader = None
_shader_uses_polyline = False
_shader_2d = None


# ── Shader helpers ─────────────────────────────────────────────────────────────

def _get_shader_3d():
    global _shader, _shader_uses_polyline
    if _shader is not None:
        return _shader
    for name, polyline in (
        ("POLYLINE_UNIFORM_COLOR", True),
        ("UNIFORM_COLOR", False),
    ):
        try:
            _shader = gpu.shader.from_builtin(name)
            _shader_uses_polyline = polyline
            return _shader
        except Exception:
            continue
    raise RuntimeError("No compatible 3D GPU line shader found")


def _get_shader_2d():
    global _shader_2d
    if _shader_2d is not None:
        return _shader_2d
    _shader_2d = gpu.shader.from_builtin("UNIFORM_COLOR")
    return _shader_2d


def _viewport_size() -> tuple[int, int]:
    vp = gpu.state.viewport_get()
    return int(vp[2]), int(vp[3])


# ── State management ──────────────────────────────────────────────────────────

def set_state(
    guide_items: list[GuideDrawItem],
    tick_items: list[GuideDrawItem],
    snap_dots: list[Vector],
    intersection_dots: list[Vector],
    labels: list[tuple[Vector, str, str]],
    *,
    active: bool,
    active_color: tuple,
    passive_color: tuple,
    line_width: float,
    solid_lines: bool,
    show_snap_dot: bool,
    snap_dot_radius_px: int,
    show_intersection_dot: bool,
    pulse_enabled: bool,
    ghost_points: list[Vector] | None = None,
):
    """Replace the active draw-handler state.

    Args:
        **kwargs: Fields of ``_State`` to assign.
    """
    s = _state
    # Pulse detection
    if active and not s.snapped_prev and pulse_enabled:
        s.pulse_frame = PULSE_FRAMES
    elif not active:
        s.pulse_frame = 0
    s.snapped_prev = active

    s.guide_items = guide_items
    s.tick_items = tick_items
    s.snap_dots = snap_dots
    s.intersection_dots = intersection_dots
    s.ghost_points = ghost_points or []
    s.labels = labels
    s.active = active
    s.active_color = active_color
    s.passive_color = passive_color
    s.line_width = line_width
    s.solid_lines = solid_lines
    s.show_snap_dot = show_snap_dot
    s.snap_dot_radius_px = snap_dot_radius_px
    s.show_intersection_dot = show_intersection_dot
    s.pulse_enabled = pulse_enabled


def clear_state():
    """Clear drawable guide state."""
    _state.guide_items = []
    _state.tick_items = []
    _state.snap_dots = []
    _state.intersection_dots = []
    _state.ghost_points = []
    _state.labels = []
    _state.active = False
    _state.snapped_prev = False
    _state.pulse_frame = 0


# ── Draw pass 1: world-space guide lines (POST_VIEW) ─────────────────────────

def _batch_colored_lines(
    shader,
    items: list[GuideDrawItem],
    solid: bool,
):
    """Draw all items grouped by colour to minimise uniform changes."""
    if not items:
        return

    # Group by colour (tuple comparison is fast for 4-tuples)
    groups: dict[tuple, list] = {}
    for item in items:
        key = item.color
        if key not in groups:
            groups[key] = []
        seg_a, seg_b = item.a, item.b
        if solid:
            # Extend a small fixed margin so the guide line reaches beyond the
            # two reference points.
            seg_a, seg_b = extend_segment(seg_a, seg_b, 0.30)
            groups[key].append(seg_a)
            groups[key].append(seg_b)
        else:
            a2, b2 = extend_segment(seg_a, seg_b, 0.25)
            for p0, p1 in dash_segments(a2, b2, dash=0.15, gap=0.10):
                groups[key].append(p0)
                groups[key].append(p1)

    vw, vh = _viewport_size()
    for color, coords in groups.items():
        if not coords:
            continue
        batch = batch_for_shader(shader, "LINES", {"pos": coords})
        shader.uniform_float("color", color)
        if _shader_uses_polyline:
            shader.uniform_float("viewportSize", (float(vw), float(vh)))
        batch.draw(shader)


def _draw_view():
    s = _state
    if not s.guide_items and not s.tick_items:
        return

    # Resolve per-frame pulse boost
    pulse_extra = 0.0
    if s.pulse_frame > 0:
        pulse_extra = PULSE_ALPHA_BOOST * (s.pulse_frame / PULSE_FRAMES)
        s.pulse_frame -= 1

    # Apply pulse to active items' alpha if needed
    items = s.guide_items
    if pulse_extra > 0.0:
        boosted = []
        for it in items:
            r, g, b, a = it.color
            boosted.append(GuideDrawItem(it.a, it.b, (r, g, b, min(1.0, a + pulse_extra))))
        items = boosted

    shader = _get_shader_3d()
    line_width = s.line_width

    gpu.state.blend_set("ALPHA")
    shader.bind()
    if _shader_uses_polyline:
        shader.uniform_float("lineWidth", line_width)
    else:
        gpu.state.line_width_set(line_width)

    _batch_colored_lines(shader, items, s.solid_lines)

    # Ticks always thin regardless of line_width
    if s.tick_items:
        if _shader_uses_polyline:
            shader.uniform_float("lineWidth", max(1.0, line_width * 0.8))
        _batch_colored_lines(shader, s.tick_items, True)

    if not _shader_uses_polyline:
        gpu.state.line_width_set(1.0)
    gpu.state.blend_set("NONE")


# ── Draw pass 2: screen-space dots + markers (POST_PIXEL) ────────────────────

def _draw_px():
    import bpy

    s = _state
    region = bpy.context.region
    rv3d = bpy.context.region_data
    if region is None or rv3d is None:
        return

    # ── Snap anchor dots ──────────────────────────────────────────────────────
    if s.show_snap_dot and s.snap_dots:
        r2d = view3d_utils.location_3d_to_region_2d
        dot_color = s.active_color
        dot_r = float(s.snap_dot_radius_px)

        circle_coords = []
        for world_pos in s.snap_dots:
            co = r2d(region, rv3d, world_pos)
            if co is None:
                continue
            for p0, p1 in circle_2d_line_pairs(co.x, co.y, dot_r, segments=20):
                circle_coords.append(p0)
                circle_coords.append(p1)
            # Inner filled-looking cross (2 short lines)
            half = dot_r * 0.35
            circle_coords.append((co.x - half, co.y))
            circle_coords.append((co.x + half, co.y))
            circle_coords.append((co.x, co.y - half))
            circle_coords.append((co.x, co.y + half))

        if circle_coords:
            shader2d = _get_shader_2d()
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader2d, "LINES", {"pos": circle_coords})
            shader2d.bind()
            shader2d.uniform_float("color", dot_color)
            batch.draw(shader2d)
            gpu.state.blend_set("NONE")

    # ── Ghost landing preview ─────────────────────────────────────────────────
    # A hollow ring showing where the selection anchor lands if released now.
    if s.ghost_points:
        r2d = view3d_utils.location_3d_to_region_2d
        ring_r = float(s.snap_dot_radius_px) * 1.8
        gr, gg, gb, ga = s.active_color
        ring_color = (gr, gg, gb, ga * 0.85)

        ring_coords = []
        for world_pos in s.ghost_points:
            co = r2d(region, rv3d, world_pos)
            if co is None:
                continue
            for p0, p1 in circle_2d_line_pairs(co.x, co.y, ring_r, segments=24):
                ring_coords.append(p0)
                ring_coords.append(p1)

        if ring_coords:
            shader2d = _get_shader_2d()
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader2d, "LINES", {"pos": ring_coords})
            shader2d.bind()
            shader2d.uniform_float("color", ring_color)
            batch.draw(shader2d)
            gpu.state.blend_set("NONE")

    # ── Intersection dots ─────────────────────────────────────────────────────
    if s.show_intersection_dot and s.intersection_dots:
        r2d = view3d_utils.location_3d_to_region_2d
        sq_color = s.active_color
        sq_half = float(s.snap_dot_radius_px) * 0.55

        sq_coords = []
        for world_pos in s.intersection_dots:
            co = r2d(region, rv3d, world_pos)
            if co is None:
                continue
            for p0, p1 in square_2d_verts(co.x, co.y, sq_half):
                sq_coords.append(p0)
                sq_coords.append(p1)

        if sq_coords:
            shader2d = _get_shader_2d()
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader2d, "LINES", {"pos": sq_coords})
            shader2d.bind()
            shader2d.uniform_float("color", sq_color)
            batch.draw(shader2d)
            gpu.state.blend_set("NONE")

    # ── BLF labels ────────────────────────────────────────────────────────────
    if not s.labels:
        return

    r2d = view3d_utils.location_3d_to_region_2d
    font_id = 0
    blf.size(font_id, 11)
    pr, pg, pb, pa = s.active_color if s.active else s.passive_color
    blf.color(font_id, pr, pg, pb, min(pa + 0.1, 1.0))

    for world_pos, primary, hint in s.labels:
        co = r2d(region, rv3d, world_pos)
        if co is None:
            continue
        blf.position(font_id, co.x + 7, co.y + 5, 0.0)
        blf.draw(font_id, primary)
        if hint:
            blf.size(font_id, 9)
            blf.color(font_id, pr, pg, pb, min(pa - 0.05, 1.0))
            blf.position(font_id, co.x + 7, co.y - 9, 0.0)
            blf.draw(font_id, hint)
            blf.size(font_id, 11)
            blf.color(font_id, pr, pg, pb, min(pa + 0.1, 1.0))


# Draw-handler wrappers restore GPU blend state on exception and log at most
# once per bound so a bad frame cannot leave ALPHA blend stuck.
_draw_errors_logged = 0
_MAX_DRAW_ERRORS_LOGGED = 3


def _reset_gpu_state():
    try:
        gpu.state.blend_set("NONE")
        gpu.state.line_width_set(1.0)
    except Exception:  # pragma: no cover - GPU module state, no headless path
        pass


def _log_draw_error(where: str):
    global _draw_errors_logged
    if _draw_errors_logged < _MAX_DRAW_ERRORS_LOGGED:
        from .. import log

        _draw_errors_logged += 1
        log.exception(f"draw error in {where}")


def _safe_draw_view():
    try:
        _draw_view()
    except Exception:
        _log_draw_error("POST_VIEW")
    finally:
        _reset_gpu_state()


def _safe_draw_px():
    try:
        _draw_px()
    except Exception:
        _log_draw_error("POST_PIXEL")
    finally:
        _reset_gpu_state()


# ── Handler registration ───────────────────────────────────────────────────────

def enable():
    """Install GPU draw handlers on the 3D View."""
    global _handle_view, _handle_px
    import bpy

    if _handle_view is None:
        _handle_view = bpy.types.SpaceView3D.draw_handler_add(
            _safe_draw_view, (), "WINDOW", "POST_VIEW"
        )
    if _handle_px is None:
        _handle_px = bpy.types.SpaceView3D.draw_handler_add(
            _safe_draw_px, (), "WINDOW", "POST_PIXEL"
        )


def disable():
    """Remove GPU draw handlers."""
    global _handle_view, _handle_px
    import bpy

    if _handle_view is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle_view, "WINDOW")
        _handle_view = None
    if _handle_px is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle_px, "WINDOW")
        _handle_px = None
    clear_state()
