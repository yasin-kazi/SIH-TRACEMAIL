"""Gmail acquisition (Phase 3).

Provides the seconds direct evidence source: OAuth connect, a read-only picker,
strict ``format=raw`` retrieval, and a ``GmailSource`` adapter that normalizes
the exact provider bytes into the existing ``AcquiredEmail`` contract. The
forensic engine is unchanged.
"""
from .gmail_source import GmailSource

__all__ = ["GmailSource"]