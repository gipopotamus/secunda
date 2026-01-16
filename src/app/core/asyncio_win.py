from __future__ import annotations

import sys


def install_windows_selector_event_loop() -> None:
    """
    psycopg (async) on Windows is incompatible with ProactorEventLoop.
    Force Selector policy for the whole process.
    """
    if sys.platform != "win32":
        return

    import asyncio  # local import for non-win speed

    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        # very old Python; not expected for 3.14
        pass
