# Development

## Environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

## Tests

Unit and integration suites are separated:

1. **Unit**: `core/` must not import `bpy`, but it does use `mathutils`,
   which has no reliable pip wheel. Run the suite inside Blender's bundled
   Python:

   ```bash
   blender --background --factory-startup --python tests/run_unit_in_blender.py
   ```

   Target coverage for `core/` is >=90%.

2. **Integration (headless Blender)**: `adapters/`, `ops/`, `draw/`, and `ui/`
   require Blender 4.2+:

   ```bash
   BLENDER_BIN=/path/to/blender .venv/bin/pytest tests/integration -m integration
   ```

   `tests/integration/test_perf_headless.py` is the speed suite. It covers
   drag start on a 400-object scene (scene cache) and Edit Mode ticks on a
   250k-vertex mesh. Each check pairs a generous time budget with a
   deterministic work count (cache hits, BVH builds, feature counts), so
   regressions are caught without flaky timings. Run it with `-s` to see the
   measured numbers.

   `tests/integration/test_release_commit_headless.py` covers the
   snap-on-release path without a window: `_begin_session`, `_tick` and
   `_commit_release` take an optional `view=(region, rv3d)`, and the test
   passes synthetic top, front and perspective views. It checks the
   translate/rotate/scale commits and their guards, multi-object and Edit Mode
   moves, the landing preview, the timer state machine, and the one-step undo
   collapse. Each simulated native transform pushes its own undo step, as
   Blender does, so `ed.undo` works in `--background`.

   `tests/integration/test_guide_noise_headless.py` is the display budget. It
   drags a cube through a grid scene and a mixed scene in top, front, right
   and perspective views and checks what the overlay draws on every frame:
   at most `max_guides` guides, one per slot; nothing that points into the
   screen in orthographic views; no equal-size or perpendicular markers
   during a move; labels only on engaged guides; intersection dots only
   between engaged lines; no duplicate strokes; enough frames engaged that
   filtering never starves snapping; and an empty overlay from the release
   frame on. Both scripts share the synthetic views in `fake_view.py`.

3. **Live (windowed Blender)**: real native modals, keymaps and drawing need
   a real event loop. `tests/live`
   starts a windowed Blender per scenario with `--enable-event-simulate`,
   drives Blender's own translate/rotate/resize modals with simulated mouse
   events, and checks the snapped result and the single undo step. Each run
   uses a throwaway `BLENDER_USER_RESOURCES`, so your Blender config is never
   touched. It needs a display, so it is opt-in:

   ```bash
   MAGNETS_LIVE=1 BLENDER_BIN=/path/to/blender .venv/bin/pytest tests/live -m live
   ```

   Set `MAGNETS_LIVE_DEBUG=1` to turn on Debug Logging in those runs, and
   `MAGNETS_LIVE_TIME_SCALE=3` to stretch the scripted timings on a slow
   machine. CI runs this suite nightly and on manual dispatch (the `live` job,
   Xvfb with software OpenGL); a failure there does not fail the workflow.

When snapping misbehaves in a real session, turn on the **Debug Logging**
preference and watch for `commit APPLIED` / `commit skip` lines in the system
console.

## Lint

```bash
.venv/bin/ruff check .
```

`ruff` is pinned in `requirements-dev.txt` because newer releases widen the
default rule set.

## Extending

### Extractors

Add an extractor in `adapters/extract.py` (or a dedicated module under `adapters/`) that yields standard `Feature` instances (`PointFeature`, `LineFeature`, etc.).

### Solvers

1. Subclass `Solver` under `core/solvers/`.
2. Implement `feature_types` / `consumes` for compatible pairs.
3. Implement `solve` to yield `Relationship` values when a constraint applies.
4. Register the instance in the loop in `core/solvers/__init__.py`.

## Packaging

```bash
python build/build_zip.py
```

Output: `dist/magnets-<version>.zip`.
