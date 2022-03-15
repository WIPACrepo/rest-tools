"""Convenience wrapper around wipac-telemetry, so package can be used with/without it."""

# pylint:skip-file

from typing import Any, Dict, Optional

try:
    import wipac_telemetry.tracing_tools as wtt
except ImportError:
    pass


def set_current_span_attribute(key: str, value: Any) -> None:
    wtt.get_current_span().set_attribute(key, value)


def inject_span_carrier_if_recording(carrier: Optional[Dict[str, Any]]) -> None:
    if wtt.get_current_span().is_recording():
        wtt.propagations.inject_span_carrier(carrier)


evented = wtt.evented
spanned = wtt.spanned
SpanNamer = wtt.SpanNamer
SpanKind = wtt.SpanKind
