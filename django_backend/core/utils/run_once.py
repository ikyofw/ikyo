import os
import threading
from typing import Callable

_run_once_flags = {}
_run_once_locks = {}
_global_lock = threading.Lock()


def run_once(
    key: str,
    func: Callable[[], None],
    *,
    only_runserver: bool = False,
    skip_autoreload: bool = True,
):
    """
    Run a function only once per Django process (thread-safe).

    This helper is useful for one-time initialization logic such as:
    - Initializing resources on first database connection
    - Registering background tasks
    - Performing lightweight startup checks

    Args:
        key: A unique identifier for the initialization task.
             It is recommended to namespace it by app name,
             e.g. "myapp:init_db".
        func: A callable with no arguments. The function contains
              the initialization logic to be executed once.
        only_runserver: If True, run only when Django is started
                        via the development server (runserver).
        skip_autoreload: If True, skip execution in the parent
                         process created by Django's autoreloader.

    Example:
        >>> from django.db.backends.signals import connection_created
        >>> from django.dispatch import receiver
        >>> from core.utils.run_once import run_once
        >>>
        >>> @receiver(connection_created, dispatch_uid="myapp:init_once")
        >>> def init_on_first_db_connection(sender, **kwargs):
        >>>     def init():
        >>>         print("Initialize something only once")
        >>>
        >>>     run_once(
        >>>         key="myapp:init_db",
        >>>         func=init,
        >>>         only_runserver=True,
        >>>     )

    Notes:
        - This function guarantees single execution only within
          the same Python process.
        - In multi-process environments (e.g. gunicorn with
          multiple workers), each process will execute once.
        - For global (cross-process) one-time execution, use
          a shared lock (e.g. Redis or database advisory lock).
    """
    if only_runserver and not _is_runserver():
        return

    if skip_autoreload and _is_autoreload_parent():
        return

    if _run_once_flags.get(key):
        return

    with _global_lock:
        if _run_once_flags.get(key):
            return

        lock = _run_once_locks.setdefault(key, threading.Lock())

    with lock:
        if _run_once_flags.get(key):
            return

        func()
        _run_once_flags[key] = True


def _is_runserver() -> bool:
    return os.environ.get("DJANGO_SETTINGS_MODULE") is not None


def _is_autoreload_parent() -> bool:
    return os.environ.get("RUN_MAIN") != "true"
