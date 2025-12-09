# core/middleware.py
from __future__ import annotations

import logging
import traceback
from typing import List

from ..utils.json_prune import prune_non_jsonable

logger = logging.getLogger(__name__)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """Return a de-duplicated list while preserving original order."""
    return list(dict.fromkeys(items))


class SessionSanitizerMiddleware:
    """
    Production-ready session sanitizer:

    - Response phase (before SessionMiddleware persists the session):
        * Unconditionally deep-prunes session data to remove/convert any
          non-JSON-serializable values; logs dropped paths (deduplicated),
          updates the session, and marks it modified. This catches nested
          mutations that happen after initial writes.

    - Request phase wrapping of session.save():
        * If session.save() raises TypeError (e.g., JSONSerializer choking on
          a custom object), snapshot, deep-prune, log dropped paths, update
          the session, mark modified, and retry the save once.

    Placement:
      - Put this middleware RIGHT AFTER
        'django.contrib.sessions.middleware.SessionMiddleware'.

    Notes:
      - This acts as a safety net. The correct long-term fix is to avoid
        storing ORM/custom objects in the session. Prefer IDs or small
        JSONable dicts.
      - Logging levels: pre-scan uses WARNING; retry-scan uses ERROR.
        Tune via Django LOGGING config as needed.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- Request phase: wrap session.save to auto-prune on failure
        sess = getattr(request, "session", None)
        if sess and not getattr(sess, "_sanitizer_save_wrapped", False):
            orig_save = sess.save

            def debug_save(*args, **kwargs):
                try:
                    return orig_save(*args, **kwargs)
                except TypeError:
                    # On save failure: snapshot, prune, log, replace, retry once
                    raw = self._snapshot_session(sess)
                    cleaned, removed = prune_non_jsonable(raw, path="")
                    if removed:
                        unique_removed = _dedupe_preserve_order(removed)
                        logger.error(
                            "[retry-scan] Session save failed -> auto-pruned %d entr%s:\n%s",
                            len(unique_removed),
                            "y" if len(unique_removed) == 1 else "ies",
                            "\n".join(f"  - {p}" for p in unique_removed),
                        )
                        self._replace_session(sess, cleaned)
                        # Retry original save once
                        return orig_save(*args, **kwargs)

                    # Nothing to prune; log stack to aid debugging, then re-raise
                    logger.error(
                        "[retry-scan] Session save failed; deep prune found nothing. "
                        "Check SESSION_SERIALIZER and custom objects.\n%s",
                        "".join(traceback.format_stack(limit=40)),
                    )
                    raise

            sess.save = debug_save
            sess._sanitizer_save_wrapped = True

        # Call the view
        response = self.get_response(request)

        # --- Response phase: unconditional pre-save prune (does not rely on `modified`)
        sess = getattr(request, "session", None)
        if sess:
            raw = self._snapshot_session(sess)
            cleaned, removed = prune_non_jsonable(raw, path="")
            if removed:
                unique_removed = _dedupe_preserve_order(removed)
                logger.warning(
                    "[pre-scan] Session pre-save auto-pruned %d entr%s:\n%s",
                    len(unique_removed),
                    "y" if len(unique_removed) == 1 else "ies",
                    "\n".join(f"  - {p}" for p in unique_removed),
                )
                self._replace_session(sess, cleaned)

        return response

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _snapshot_session(sess) -> dict:
        """
        Snapshot current session data into a plain dict without forcing JSON serialization.
        """
        try:
            return dict(sess.items())
        except Exception:
            # Fallback to private cache if items() fails for a backend
            return getattr(sess, "_session_cache", {}) or {}

    @staticmethod
    def _replace_session(sess, cleaned: dict) -> None:
        """
        Replace current session content with `cleaned` and mark it modified.
        """
        sess.clear()
        if cleaned:
            sess.update(cleaned)
        sess.modified = True  # ensure Django persists the new content
