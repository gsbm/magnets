# Usage

## Requirements

- Blender 4.2 LTS or newer.

## How it works

Magnets draws smart guides while you move, rotate, or scale with `G`, `R`, and
`S` in the 3D Viewport. You keep using Blender's own transform. Magnets never
replaces the keys unless you turn on Precision Mode.

### Default: snap on release

- **While dragging**: guides fade in as the selection nears a relationship
  (alignment, even spacing, midpoints, and so on). A guide turns solid and gets
  a label when it engages. For moves, a ring marks where the selection will
  land.
- **On release**: the selection snaps to the engaged guides. In Object Mode the
  move and the snap are a single undo step. In Edit Mode the snap is a second
  step.
- **Rotate** snaps to the nearest angle increment (Angle Snap, default 15°) if
  you release close to one. **Scale** matches a nearby object's size if you
  release close to it.
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

## Sidebar panel

3D Viewport sidebar (`N`) ▸ **Magnets**. The header checkbox turns Magnets on or
off for the scene.

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
- **Colors and lines**: passive and active guide colors, line width, solid or
  dashed lines.
- **Indicators**: proximity fade, engage pulse, intersection marker, and the
  snap anchor dot.
- **Debug Logging**: prints session, per-frame, and commit diagnostics to the
  system console. Use it when snapping misbehaves.
