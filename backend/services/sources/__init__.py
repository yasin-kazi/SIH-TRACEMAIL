"""Email source acquisition layer.

Defines the common capture contract: any acquisition adapter (EML file, Gmail,
Microsoft 365, raw message, header paste) produces one normalized ``AcquiredEmail``
that the forensic pipeline consumes. The pipeline never cares which source an
email came from.
"""
from .email_source import EmailSource, AcquiredEmail
from .eml_source import EMLSource

__all__ = ["EmailSource", "AcquiredEmail", "EMLSource"]