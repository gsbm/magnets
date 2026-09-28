SHELL := /bin/sh

# Run `make` with no args to see the human-facing commands.
.DEFAULT_GOAL := help

# ── Settings ──────────────────────────────────────────────────────────────────
# Blender binary for the unit / integration / live suites.
BLENDER ?= /Applications/Blender.app/Contents/MacOS/Blender

DIST := dist

# The manifest is the one copy of the version (build/build_zip.py reads it too).
VERSION = $(shell sed -n 's/^version *= *"\(.*\)"/\1/p' magnets/blender_manifest.toml)

# Prefer tools on PATH; otherwise uvx (uv caches the binary after first fetch).
RUFF   = $(shell command -v ruff >/dev/null 2>&1 && echo ruff || echo uvx ruff)
PYTEST = $(shell command -v pytest >/dev/null 2>&1 && echo pytest || echo uvx pytest)

.PHONY: help dist format lint test test-fast test-live clear require-blender require-ruff

help:
	@echo ""
	@echo "  Build"
	@echo "    make dist          extension zip -> $(DIST)/magnets-$(VERSION).zip"
	@echo ""
	@echo "  Code"
	@echo "    make format        ruff format + import sorting"
	@echo "    make lint          ruff check (same as CI)"
	@echo ""
	@echo "  Tests  [BLENDER=/path/to/blender]"
	@echo "    make test          unit (in Blender's Python) + headless integration"
	@echo "    make test-fast     unit suite only"
	@echo "    make test-live     windowed live suite (needs a display; slow)"
	@echo ""
	@echo "  Housekeeping"
	@echo "    make clear         remove $(DIST)/, caches and coverage leftovers"
	@echo ""

require-blender:
	@test -x "$(BLENDER)" || command -v "$(BLENDER)" >/dev/null 2>&1 || { \
		echo "  ✗ Blender not found at $(BLENDER) -- pass BLENDER=/path/to/blender"; exit 1; }

require-ruff:
	@command -v ruff >/dev/null 2>&1 || command -v uvx >/dev/null 2>&1 || { \
		echo "  ✗ need ruff or uvx -- brew install ruff  |  https://docs.astral.sh/uv/"; exit 1; }

# ── Build ─────────────────────────────────────────────────────────────────────
# Manifest at the zip root (4.2 Extensions); needs no Blender binary.
dist:
	@command -v python3 >/dev/null 2>&1 || { echo "  ✗ python3 not found"; exit 1; }
	@python3 build/build_zip.py

# ── Code style ────────────────────────────────────────────────────────────────
format: require-ruff
	@$(RUFF) check --select I --fix .
	@$(RUFF) format .
	@echo "  formatted."

lint: require-ruff
	@$(RUFF) check .
	@echo "  ok."

# ── Tests ─────────────────────────────────────────────────────────────────────
# Unit tests import mathutils, so they run inside Blender's bundled Python
# rather than pytest; the grep mirrors CI's pass check.
test-fast: require-blender
	@echo "==> unit (Blender's Python)"
	@"$(BLENDER)" --background --factory-startup --python tests/run_unit_in_blender.py 2>&1 \
		| tee /tmp/magnets_unit.log | grep -E 'passed|failed|Error' ; \
	grep -qE '[0-9]+ passed, 0 failed' /tmp/magnets_unit.log || { \
		echo "  ✗ unit suite failed -- full log: /tmp/magnets_unit.log"; exit 1; }

test: test-fast
	@echo "==> integration (headless Blender)"
	@BLENDER_BIN="$(BLENDER)" $(PYTEST) tests/integration -m integration -q

test-live: require-blender
	@echo "==> live (windowed Blender, simulated input)"
	@MAGNETS_LIVE=1 BLENDER_BIN="$(BLENDER)" $(PYTEST) tests/live -m live -q -rA

# ── Housekeeping ──────────────────────────────────────────────────────────────
# Build/test leftovers only; never touches venvs or .claude/.
clear:
	@rm -rf $(DIST) .pytest_cache .ruff_cache coverage .coverage .coverage.*
	@find . -name __pycache__ -type d -prune -not -path './venv*' -not -path './.venv*' -exec rm -rf {} +
	@rm -f /tmp/magnets_unit.log
	@echo "  cleared."
