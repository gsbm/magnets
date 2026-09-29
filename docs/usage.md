# Usage

## Requirements

- Blender 4.2 LTS or newer.

## How it works

Magnets draws smart guides while you move, rotate, or scale with `G`, `R`, and
`S` in the 3D Viewport. You keep using Blender's own transform. Magnets never
replaces the keys unless you turn on Precision Mode.

### Default: snap on release

- **While dragging**: guides fade in, in a quiet neutral color, as the
  selection nears a relationship (alignment, even spacing, midpoints, and so
  on). When a guide engages it turns bold, flashes briefly, and gets a label.
  Engaged alignment guides take Blender's axis colors (X red, Y green, Z blue).
  A dashed outline shows exactly where the selection will land on release.
- **On release**: the selection snaps to the engaged guides. In Object Mode the
  move and the snap are a single undo step. In Edit Mode the snap is a second
  step.
- **Rotate** snaps to the nearest angle increment (Angle Snap, default 15°) if
  you release close to one. **Scale** matches a nearby object's size if you
  release close to it. Both preview while you drag: a dashed outline of the
  final pose plus a note at the pivot (the rotate icon and `45°`, or the equal-size icon and `Cube.002 · 2 m`). No note
  means no snap will happen.
- **Cancel** (`Esc` or right-click) never snaps.
- **Axis locks** (`G X`, `G Shift+Z`) are respected: the snap only moves along
  the locked axes. In an orthographic view the snap never changes depth.

### Precision Mode

Turn it on in the Magnets sidebar panel or in the add-on preferences. `G`, `R`,
and `S` then run Magnets' own operators, which lock onto a guide *while* you
drag. They support `X`/`Y`/`Z` axis locks and mouse-wheel zoom. They do not
support numeric input, orbiting mid-drag, or proportional editing. Edit-mode
rotate and scale fall back to Blender's transform.

### Working with Blender snapping

When Blender's own snapping is on (the magnet icon in the viewport header),
Magnets stands aside: it hides its guides and does not snap, so the two never
fight. Holding `Ctrl` to snap with Blender for a single move also skips the
Magnets snap on release, though its guides still show during that drag. Turn off
**Snapping ▸ Blender Snap ▸ Yield** to have Magnets snap regardless.

## Turning Magnets on and off

- **Header button**: the magnet button at the right of the 3D Viewport header
  turns Magnets on or off. Its arrow opens a compact settings popover.
- **Shortcut**: `Shift Alt M` toggles Magnets. Rebind it in the add-on
  preferences, or right-click the header button.
- The sidebar panel's header checkbox does the same.

## Sidebar panel

3D Viewport sidebar (`N`) ▸ **Magnets**.

- **Snap to Guides**: off shows guides without snapping.
- **Precision Mode**: see above. A line under it summarises what `G`/`R`/`S`
  will do.
- **Presets**: Precise, Balanced (the defaults), and Loose tolerance profiles.
  The active preset is highlighted. The reset button restores every scene
  option.
- **Snapping**: snap tolerance, break distance, re-engage gap, angle snap,
  even-spacing metric, and whether to yield to Blender snapping.
- **Guides**: range, maximum guides, spacing between guides, what to show,
  proximity fade, and viewport-length lines.
- **Alignment**: the reference frame (World, Local, View, Parent, Collection,
  or a Custom object), the allowed axes, and which reference points count.
- **Guide Types**: turn individual relationship families on or off.

Pixel tolerances follow Blender's Resolution Scale, so they feel the same on
HiDPI displays. Distances in labels use the scene's unit system.

## Preferences

Edit ▸ Preferences ▸ Add-ons ▸ Magnets:

- **Precision Mode**: same toggle as in the sidebar.
- **Header Toggle**: show or hide the header button.
- **Colors and lines**: passive and active guide colors, Engaged Colors (axis
  colors, or the Active Color for every guide), line width, solid or dashed
  lines. Dashes and guide lengths follow the viewport zoom, so they look the
  same at any scene scale.
- **Indicators**: proximity fade, engage pulse, intersection marker, and the
  snap anchor dot.
- **Shortcut**: rebind the on/off toggle.
- **Debug Logging**: prints session, per-frame, and commit diagnostics to the
  system console. Use it when snapping misbehaves.
