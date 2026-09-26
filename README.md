# Magnets

Blender add-on for geometric relationship snapping during viewport transforms (translate, rotate, scale).

## Documentation

- [Architecture](docs/architecture.md): package layout, data pipeline, solvers
- [Development](docs/development.md): setup, tests, extending extractors and solvers
- [Usage](docs/usage.md): how snapping works, sidebar options, preferences

## Layout

```text
magnets/    Add-on source. core/ has no bpy dependency.
build/      Packaging (build_zip.py).
tests/      bpy-free unit tests and headless Blender integration tests.
docs/       Technical documentation.
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .                # lint
python3 build/build_zip.py            # write dist/magnets-<version>.zip
```

### Tests

The unit suite imports `mathutils`, which has no reliable pip wheel, so it
runs inside Blender's bundled Python:

```bash
blender --background --factory-startup --python tests/run_unit_in_blender.py
```

Integration tests drive a headless Blender (4.2+) from pytest:

```bash
BLENDER_BIN=/path/to/blender .venv/bin/pytest tests/integration -m integration
```

### Install in Blender

1. Run `python build/build_zip.py`.
2. Open Blender 4.2 LTS or newer.
3. Edit > Preferences > Get Extensions > Install from Disk.
4. Select `dist/magnets-<version>.zip`.
