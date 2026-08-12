# Development

## Environment

```bash
pip install -r requirements-dev.txt
```

## Tests

Unit and integration suites are separated:

1. **Unit (no Blender)**: `core/` must not import `bpy`. Run:

   ```bash
   pytest tests/unit
   ```

   Target coverage for `core/` is >=90%.

2. **Integration (headless Blender)**: `adapters/`, `ops/`, and `draw/` require Blender 4.2+:

   ```bash
   BLENDER_BIN=/path/to/blender pytest tests/integration -m integration
   ```

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
