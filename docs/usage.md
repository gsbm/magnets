# Usage

## Requirements

- Blender 4.2 LTS or newer.

## Operators

In the 3D Viewport, Magnets binds `G`, `R`, and `S` to modal operators:

- **Translate (G)**: Alignment, spacing, midpoint, and bounding-box snaps.
- **Rotate (R)**: Angle increments and orientation guides.
- **Scale (S)**: Equal-size constraints against targets.

Confirm with the primary mouse button. Cancel with Escape or the secondary mouse button (no undo push). In Object Mode, confirm commits one undo step.

## N-Panel

3D Viewport sidebar > **Magnets**:

- **Global toggles**: Enable or disable constraint families.
- **Tolerances**: Screen-space snap distance (pixels) and angular thresholds.
- **Presets**: Precise, Balanced, Loose tolerance profiles.

## Preferences

Edit > Preferences > Extensions > Magnets:

- **Visuals**: Guide colors, thickness, and style.
- **Precision Mode**: Require an explicit key to engage guides instead of automatic snap.
- **Debug Logging**: Pipeline and solver timing on the system console.
