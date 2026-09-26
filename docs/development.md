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

The release path of the native-transform overlay (`transform_overlay.py`)
needs a live event loop, so it cannot run headless. Check it by hand with the
**Debug Logging** preference on, watching for `commit APPLIED` / `commit skip`
lines in the system console.

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
