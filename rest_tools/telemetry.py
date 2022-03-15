"""Convenience wrapper around wipac-telemetry, so package can be used with/without it."""

# pylint:skip-file

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

#
# First, try to import then implement wipac-telemetry
#
try:
    import wipac_telemetry.tracing_tools as wtt

    evented = wtt.evented
    spanned = wtt.spanned
    SpanNamer = wtt.SpanNamer
    SpanKind = wtt.SpanKind

    def set_current_span_attribute(key: str, value: Any) -> None:
        wtt.get_current_span().set_attribute(key, value)

    def inject_span_carrier_if_recording(carrier: Optional[Dict[str, Any]]) -> None:
        if wtt.get_current_span().is_recording():
            wtt.propagations.inject_span_carrier(carrier)


#
# Otherwise, dummy-implement every call
#
except ImportError:

    # fmt: off
    FuncT = TypeVar("FuncT", bound=Callable[..., Any])

    def evented(func: FuncT) -> FuncT:  # type: ignore[misc]
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return cast(FuncT, wrapped)

    def spanned(func: FuncT) -> FuncT:  # type: ignore[misc]
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return cast(FuncT, wrapped)
    # fmt:on

    def dummy_func(*args: Any, **kwargs: Any) -> None:
        pass

    class DummyClass:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    SpanNamer = DummyClass  # type: ignore[assignment, misc]

    class SpanKind(Enum):  # type: ignore[no-redef]
        INTERNAL = 0
        SERVER = 1
        CLIENT = 2
        PRODUCER = 3
        CONSUMER = 4

    set_current_span_attribute = dummy_func
    inject_span_carrier_if_recording = dummy_func
