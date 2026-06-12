"""MyHoudiniTools-side console filter for FXHoudini-MCP startup noise.

This patch intentionally does only one thing: suppress selected original
``fxhoudinimcp`` console prints. It does not change MCP startup, hwebserver,
health checks, retries, ports, or any plugin behavior.

Disable with ``MYTOOLS_FXHOUDINIMCP_FILTER_LOGS=0``.
"""

from __future__ import annotations

import builtins
import os


_PRINT_PATCH_MARKER = "_mytools_fxhoudinimcp_print_patch"
_ORIGINAL_PRINT_ATTR = "_mytools_fxhoudinimcp_original_print"


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value not in {"0", "false", "False", "no", "No", "off", "Off"}


def _print_message(args: tuple[object, ...], kwargs: dict[str, object]) -> str:
    sep = kwargs.get("sep", " ")
    if sep is None:
        sep = " "
    return str(sep).join(str(arg) for arg in args)


def _should_suppress(message: str) -> bool:
    if not _env_bool("MYTOOLS_FXHOUDINIMCP_FILTER_LOGS", True):
        return False

    if message.startswith("[fxhoudinimcp] Loaded ") and " handler modules " in message:
        return True

    if message.startswith(
        "[fxhoudinimcp] Auto-start failed: hwebserver did not answer mcp.health on port "
    ):
        return True

    return False


def install() -> None:
    """Install the narrow print filter once."""
    current_print = builtins.print
    if getattr(current_print, _PRINT_PATCH_MARKER, False):
        return

    original_print = getattr(builtins, _ORIGINAL_PRINT_ATTR, current_print)

    def filtered_print(*args, **kwargs):  # noqa: ANN002, ANN003 - mirrors print()
        try:
            if _should_suppress(_print_message(args, kwargs)):
                return None
        except Exception:
            pass
        return original_print(*args, **kwargs)

    setattr(filtered_print, _PRINT_PATCH_MARKER, True)
    setattr(builtins, _ORIGINAL_PRINT_ATTR, original_print)
    builtins.print = filtered_print


install()
