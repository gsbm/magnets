# Architecture

Magnets is a Blender add-on for geometric relationship snapping in the 3D
Viewport. Inference logic under `core/` has no `bpy` dependency and uses
`mathutils` and `numpy` only.

## Transform Paths

- **Default, snap on release** (`transform_overlay.py`): a `bpy.app.timers`
  loop watches Blender's native `TRANSFORM_OT_*` operators. During the drag it
  only draws guides and a landing ring. When the transform is released it
  re-runs inference once, applies the snap, and folds it into the transform's
  undo step. It stands aside when Blender's own snapping is active.
- **Precision Mode** (`ops/modal_*.py`): opt-in keymap items bind `G`/`R`/`S`
  to Magnets' modal operators, which own the transform and lock onto guides
  while dragging.

## Data Pipeline

Each inference tick (a timer frame or a modal `MOUSEMOVE`) runs:

1. **Extraction**: Scene elements (`Entity`) become geometric primitives (`Feature`).
2. **Dispatch**: Feature pairs go to solvers by type.
3. **Solving**: Solvers emit `Relationship` values with a `ConstraintDelta` and `Guide`.
4. **Ranking**: Candidates are scored (screen distance, residual, family weight); slot suppression removes duplicates.
5. **Resolution**: Top constraints become a transform offset applied to preview/commit state.

```mermaid
flowchart LR
  Entity -->|extract| Feature
  Feature -->|solve| Relationship
  Relationship --> Marker
```

## Data Models

Core pipeline state uses typed dataclasses:

- `Entity`: Participant in inference (object, vertex, edge, etc.).
- `Feature`: Primitive (`PointFeature`, `LineFeature`, `PlaneFeature`, `DirectionFeature`, `CircleFeature`, `BBoxFeature`).
- `Relationship`: Solver output: targets, residual, `ConstraintDelta`, and `Guide`.
- `SolveContext`: Tolerances, axes, transform mode, and related constants.

## Package Layout

```mermaid
flowchart TB
  ops["ops/ modal operators"]
  adapters["adapters/ bpy bridges"]
  core["core/ bpy-free inference"]
  draw["draw/ GPU guides"]
  ui["ui/ N-panel"]

  ops --> adapters
  ops --> core
  ops --> draw
  adapters --> core
  draw --> core
  ui --> ops
```

- `core/features.py`: Feature dataclasses.
- `core/relationship.py`: `Relationship` and `ConstraintDelta`.
- `core/solvers/`: Solvers implementing the `Solver` ABC.
- `core/resolver.py`: Merge constraints into translation / rotation / scale.
- `core/spatial.py`: KDTree and hash-grid broad phase.
- `adapters/`: Map `bpy` types to `Entity` / `Feature`.
- `ops/`: Modal operators and the shared inference pipeline.
- `draw/`: GPU guide rendering.
