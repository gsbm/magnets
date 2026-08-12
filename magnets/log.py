"""Central logger for Magnets."""

from __future__ import annotations

import logging

_logger = logging.getLogger("magnets")
_logger.setLevel(logging.WARNING)

if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[Magnets] %(message)s"))
    _logger.addHandler(_handler)
    _logger.propagate = False


def set_debug(enabled: bool) -> None:
    """Match log verbosity to the Debug Logging preference."""
    _logger.setLevel(logging.DEBUG if enabled else logging.WARNING)


def debug_enabled() -> bool:
    """True when DEBUG logging is enabled."""
    return _logger.isEnabledFor(logging.DEBUG)


def debug(msg: str) -> None:
    """Log a debug message."""
    _logger.debug(msg)


def warning(msg: str) -> None:
    """Log a warning message."""
    _logger.warning(msg)


def exception(msg: str) -> None:
    """Log an error with the current traceback (call from an except block)."""
    _logger.exception(msg)
