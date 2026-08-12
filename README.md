# Magnets

Blender add-on for geometric relationship snapping during viewport transforms (translate, rotate, scale).

## Documentation

- [Architecture](docs/architecture.md): package layout, data pipeline, solvers
- [Development](docs/development.md): setup, tests, extending extractors and solvers
- [Usage](docs/usage.md): operators, N-panel options, preferences

## Layout

```text
magnets/    Add-on source. core/ has no bpy dependency.
build/      Packaging (build_zip.py).
tests/      bpy-free unit tests and headless Blender integration tests.
docs/       Technical documentation.
```

## Setup

```bash
pip install -r requirements-dev.txt
pytest                      # bpy-free unit tests
ruff check .                # lint
python build/build_zip.py   # write dist/magnets-<version>.zip
```

### Integration tests

Requires Blender 4.2+.

```bash
BLENDER_BIN=/path/to/blender pytest tests/integration -m integration
```

### Install in Blender

1. Run `python build/build_zip.py`.
2. Open Blender 4.2 LTS or newer.
3. Edit > Preferences > Get Extensions > Install from Disk.
4. Select `dist/magnets-<version>.zip`.
