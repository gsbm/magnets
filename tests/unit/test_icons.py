"""Guide icons follow Blender's icon grid rules and stay in sync with the site."""

from itertools import pairwise
from pathlib import Path

from core.families import FAMILY_IDS
from core.icons import AREA, CANVAS, ICONS, STROKE, geometry, icon_for_family, sprite

REPO = Path(__file__).resolve().parents[2]


def _extent(part):
    if part.kind in ("line", "poly"):
        return list(part.geo), STROKE / 2
    if part.kind in ("ring", "arc"):
        (cx, cy), r = part.geo[0], part.geo[1]
        return [(cx - r, cy - r), (cx + r, cy + r)], STROKE / 2
    (cx, cy), r = part.geo
    return [(cx - r, cy - r), (cx + r, cy + r)], 0.0


def test_every_icon_stays_inside_the_one_cell_margin():
    lo, hi = AREA
    for icon_id, parts in ICONS.items():
        for part in parts:
            points, pad = _extent(part)
            for x, y in points:
                assert lo - 1e-6 <= x - pad and x + pad <= hi + 1e-6, (icon_id, part.kind, x)
                assert lo - 1e-6 <= y - pad and y + pad <= hi + 1e-6, (icon_id, part.kind, y)


def test_two_tones_and_a_primary_part_in_every_icon():
    for icon_id, parts in ICONS.items():
        assert {p.tone for p in parts} <= {"p", "s"}, icon_id
        assert any(p.tone == "p" for p in parts), f"{icon_id} has no primary (selection) part"


def test_straight_lines_sit_on_half_cells_for_crisp_pixels():
    # Axis-aligned stroke segments must lie on x50 coordinates at 16 px.
    for icon_id, parts in ICONS.items():
        for part in parts:
            if part.kind not in ("line", "poly"):
                continue
            pts = list(part.geo) + ([part.geo[0]] if part.kind == "poly" else [])
            for (x0, y0), (x1, y1) in pairwise(pts):
                if x0 == x1:
                    assert x0 % 100 == 50, (icon_id, "vertical line off the pixel grid", x0)
                if y0 == y1:
                    assert y0 % 100 == 50, (icon_id, "horizontal line off the pixel grid", y0)


def test_every_guide_family_but_alignment_has_an_icon():
    for fid in FAMILY_IDS:
        if fid == "alignment":
            assert icon_for_family(fid) is None
        else:
            assert icon_for_family(fid) == fid, fid
    assert "rotate" in ICONS


def test_viewport_geometry_fits_its_box():
    x, y, size = 10.0, 20.0, 16.0
    for icon_id in ICONS:
        lines, fills, width = geometry(icon_id, x, y, size)
        assert width == size / CANVAS * STROKE
        for tone in ("p", "s"):
            assert len(lines[tone]) % 2 == 0 and len(fills[tone]) % 3 == 0
            for px, py in lines[tone] + fills[tone]:
                assert x - 1e-6 <= px <= x + size + 1e-6 and y - 1e-6 <= py <= y + size + 1e-6, icon_id
        assert lines["p"] or fills["p"], icon_id


def test_landing_sprite_is_generated_from_these_icons():
    committed = (REPO / "landing" / "icons.svg").read_text(encoding="utf-8")
    assert committed == sprite(), "landing/icons.svg is stale: run python build/export_icons.py"
    for icon_id in ICONS:
        assert f'id="i-{icon_id}"' in committed
