"""GPU draw handlers for the 3D View."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import blf
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from ..adapters.view import pixel_size, ui_scale
from ..core.style import (
    ACTIVE_WIDTH_SCALE,
    pulse_strength,
    pulsed_color,
    pulsed_width,
)
from .glyphs import (
    circle_2d_line_pairs,
    dash_segments,
    extend_segment,
    square_2d_verts,
)

Color = tuple[float, float, float, float]

# Hard cap on dashes per segment; beyond it dashes lengthen instead.
_MAX_DASHES = 600

# ── Internal state ─────────────────────────────────────────────────────────────

@dataclass
class GuideDrawItem:
    """One guide segment + its per-item render colour (includes fade alpha)."""
    a: Vector
    b: Vector
    color: Color  # linear RGBA, already faded
    active: bool = False  # engaged: drawn thicker and pulsed on engage


@dataclass
class _State:
    """Mutable GPU draw-handler state."""
    guide_items: list[GuideDrawItem] = field(default_factory=list)
    tick_items: list[GuideDrawItem] = field(default_factory=list)
    # Landing preview: bounding-box outlines of the snapped pose (dashed).
    ghost_edges: list[tuple[Vector, Vector]] = field(default_factory=list)

    # Screen-space markers (world positions → projected in _draw_px)
    snap_dots: list[tuple[Vector, Color]] = field(default_factory=list)  # circles
    intersection_dots: list[Vector] = field(default_factory=list)  # squares
    ghost_points: list[Vector] = field(default_factory=list)  # landing ring
    labels: list[tuple[Vector, str, str, Color]] = field(default_factory=list)

    # Preferences snapshot (set each frame via set_state)
    active_color: Color = (1.0, 0.2, 0.75, 1.0)
    passive_color: Color = (0.85, 0.87, 0.92, 0.5)
    line_width: float = 1.0
    solid_lines: bool = True
    show_snap_dot: bool = True
    snap_dot_radius_px: int = 4
    show_intersection_dot: bool = True
    pulse_enabled: bool = True
    # World length of one dash / gap, sized from the viewport zoom so dashes
    # read the same at millimetre and kilometre scale.
    dash_world: float = 0.15
    gap_world: float = 0.10

    # Pulse state: wall-clock start of the current engage flash.
    snapped_prev: bool = False
    pulse_start: float | None = None

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
        except (ValueError, TypeError):  # shader not available on this build
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
    snap_dots: list[tuple[Vector, Color]],
    intersection_dots: list[Vector],
    labels: list[tuple[Vector, str, str, Color]],
    *,
    active: bool,
    active_color: Color,
    passive_color: Color,
    line_width: float,
    solid_lines: bool,
    show_snap_dot: bool,
    snap_dot_radius_px: int,
    show_intersection_dot: bool,
    pulse_enabled: bool,
    ghost_points: list[Vector] | None = None,
    ghost_edges: list[tuple[Vector, Vector]] | None = None,
    dash_world: float | None = None,
    gap_world: float | None = None,
):
    """Replace the active draw-handler state.

    Args:
        **kwargs: Fields of ``_State`` to assign.
    """
    s = _state
    # Pulse detection: flash once on the frame a guide engages.
    if active and not s.snapped_prev and pulse_enabled:
        s.pulse_start = time.monotonic()
    elif not active:
        s.pulse_start = None
    s.snapped_prev = active

    s.guide_items = guide_items
    s.tick_items = tick_items
    s.snap_dots = snap_dots
    s.intersection_dots = intersection_dots
    s.ghost_points = ghost_points or []
    s.ghost_edges = ghost_edges or []
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
    if dash_world is not None and dash_world > 0.0:
        s.dash_world = dash_world
    if gap_world is not None and gap_world > 0.0:
        s.gap_world = gap_world


def clear_state():
    """Clear drawable guide state."""
    _state.guide_items = []
    _state.tick_items = []
    _state.ghost_edges = []
    _state.snap_dots = []
    _state.intersection_dots = []
    _state.ghost_points = []
    _state.labels = []
    _state.active = False
    _state.snapped_prev = False
    _state.pulse_start = None


# ── Draw pass 1: world-space guide lines (POST_VIEW) ─────────────────────────

def _add_segment(groups: dict, key: tuple, a: Vector, b: Vector, *, dashed: bool,
                 extend: float = 0.0):
    """Append a segment (or its dashes) to the ``(color, width)`` group."""
    coords = groups.setdefault(key, [])
    if extend > 0.0:
        a, b = extend_segment(a, b, extend)
    if not dashed:
        coords.append(a)
        coords.append(b)
        return
    s = _state
    for p0, p1 in dash_segments(
        a, b, dash=s.dash_world, gap=s.gap_world, max_count=_MAX_DASHES
    ):
        coords.append(p0)
        coords.append(p1)


def _draw_groups(shader, groups: dict):
    """Draw ``{(color, width): coords}`` with one batch per group."""
    vw, vh = _viewport_size()
    for (color, width), coords in groups.items():
        if not coords:
            continue
        batch = batch_for_shader(shader, "LINES", {"pos": coords})
        shader.uniform_float("color", color)
        if _shader_uses_polyline:
            shader.uniform_float("viewportSize", (float(vw), float(vh)))
            shader.uniform_float("lineWidth", width)
        else:
            gpu.state.line_width_set(width)
        batch.draw(shader)


def _pulse_now(context) -> float:
    """Current engage-pulse strength; keeps the viewport redrawing until done."""
    s = _state
    if s.pulse_start is None:
        return 0.0
    strength = pulse_strength(time.monotonic() - s.pulse_start)
    if strength > 0.0:
        area = getattr(context, "area", None)
        if area is not None:
            area.tag_redraw()
    return strength


def _draw_view():
    s = _state
    if not s.guide_items and not s.tick_items and not s.ghost_edges:
        return

    import bpy

    strength = _pulse_now(bpy.context)
    base_width = s.line_width * pixel_size(bpy.context)

    groups: dict[tuple, list] = {}
    for it in s.guide_items:
        color, width = it.color, base_width
        if it.active:
            width = pulsed_width(width * ACTIVE_WIDTH_SCALE, strength)
            color = pulsed_color(color, strength)
        # Extend a little so the line reaches past its two reference points.
        _add_segment(groups, (color, width), it.a, it.b,
                     dashed=not s.solid_lines, extend=0.3)

    # Ticks stay thin regardless of line width.
    tick_width = max(1.0, base_width * 0.8)
    for it in s.tick_items:
        _add_segment(groups, (it.color, tick_width), it.a, it.b,
                     dashed=False, extend=0.3)

    # Landing preview: dashed so it never reads as real geometry.
    if s.ghost_edges:
        r, g, b, a = s.active_color
        ghost_key = ((r, g, b, a * 0.8), base_width)
        for ga, gb in s.ghost_edges:
            _add_segment(groups, ghost_key, ga, gb, dashed=True)

    shader = _get_shader_3d()
    gpu.state.blend_set("ALPHA")
    shader.bind()
    _draw_groups(shader, groups)

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
    # Screen sizes are authored at 1x; follow Blender's UI scale (HiDPI).
    scale = ui_scale(bpy.context)

    # ── Snap anchor dots ──────────────────────────────────────────────────────
    if s.show_snap_dot and s.snap_dots:
        r2d = view3d_utils.location_3d_to_region_2d
        dot_r = float(s.snap_dot_radius_px) * scale

        # Each dot takes its guide's colour; group to one batch per colour.
        dot_groups: dict[tuple, list] = {}
        for world_pos, dot_color in s.snap_dots:
            co = r2d(region, rv3d, world_pos)
            if co is None:
                continue
            circle_coords = dot_groups.setdefault(dot_color, [])
            for p0, p1 in circle_2d_line_pairs(co.x, co.y, dot_r, segments=20):
                circle_coords.append(p0)
                circle_coords.append(p1)
            # Inner filled-looking cross (2 short lines)
            half = dot_r * 0.35
            circle_coords.append((co.x - half, co.y))
            circle_coords.append((co.x + half, co.y))
            circle_coords.append((co.x, co.y - half))
            circle_coords.append((co.x, co.y + half))

        if dot_groups:
            shader2d = _get_shader_2d()
            gpu.state.blend_set("ALPHA")
            shader2d.bind()
            for dot_color, circle_coords in dot_groups.items():
                batch = batch_for_shader(shader2d, "LINES", {"pos": circle_coords})
                shader2d.uniform_float("color", dot_color)
                batch.draw(shader2d)
            gpu.state.blend_set("NONE")

    # ── Ghost landing preview ─────────────────────────────────────────────────
    # A hollow ring showing where the selection anchor lands if released now.
    if s.ghost_points:
        r2d = view3d_utils.location_3d_to_region_2d
        ring_r = float(s.snap_dot_radius_px) * 1.8 * scale
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
        sq_half = float(s.snap_dot_radius_px) * 0.55 * scale

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

    _draw_labels(region, rv3d, scale)


def _draw_labels(region, rv3d, scale: float):
    """Draw guide labels with a drop shadow so they read over any geometry."""
    s = _state
    r2d = view3d_utils.location_3d_to_region_2d
    font_id = 0
    main_size = 11.0 * scale
    hint_size = 9.0 * scale
    dx = 7.0 * scale

    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 0.85)
    blf.shadow_offset(font_id, 1, -1)
    try:
        for world_pos, primary, hint, color in s.labels:
            co = r2d(region, rv3d, world_pos)
            if co is None:
                continue
            pr, pg, pb, pa = color
            blf.size(font_id, main_size)
            blf.color(font_id, pr, pg, pb, min(pa + 0.1, 1.0))
            blf.position(font_id, co.x + dx, co.y + 5.0 * scale, 0.0)
            blf.draw(font_id, primary)
            if hint:
                blf.size(font_id, hint_size)
                blf.color(font_id, pr, pg, pb, max(pa - 0.05, 0.0))
                blf.position(font_id, co.x + dx, co.y - 9.0 * scale, 0.0)
                blf.draw(font_id, hint)
    finally:
        blf.disable(font_id, blf.SHADOW)


# Draw-handler wrappers restore GPU blend state on exception and log at most
# once per bound so a bad frame cannot leave ALPHA blend stuck.
_draw_errors_logged = 0
_MAX_DRAW_ERRORS_LOGGED = 3


def _reset_gpu_state():
    try:
        gpu.state.blend_set("NONE")
        gpu.state.line_width_set(1.0)
    except Exception:  # noqa: BLE001, S110 - GPU state, no headless path
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
    except Exception:  # noqa: BLE001 - a draw error must not escape
        _log_draw_error("POST_VIEW")
    finally:
        _reset_gpu_state()


def _safe_draw_px():
    try:
        _draw_px()
    except Exception:  # noqa: BLE001 - a draw error must not escape
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
