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

3. **Live (windowed Blender)**: the release path of the native-transform
   overlay (`transform_overlay.py`) needs a real event loop. `tests/live`
   starts a windowed Blender per scenario with `--enable-event-simulate`,
   drives Blender's own translate/rotate/resize modals with simulated mouse
   events, and checks the snapped result and the single undo step. Each run
   uses a throwaway `BLENDER_USER_RESOURCES`, so your Blender config is never
   touched. It needs a display, so it is opt-in:

   ```bash
   MAGNETS_LIVE=1 BLENDER_BIN=/path/to/blender .venv/bin/pytest tests/live -m live
   ```

   Set `MAGNETS_LIVE_DEBUG=1` to turn on Debug Logging in those runs.

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
