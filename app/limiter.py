"""Shared rate-limiter instance (slowapi).

Defined here to avoid circular imports between main.py and routes.py.
The limiter is keyed by remote IP address.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
